import csv
import logging
from argparse import ArgumentParser
from typing import Any
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from typing_extensions import override

from zerver.actions.create_user import do_create_user
from zerver.lib.management import ZulipBaseCommand

logger = logging.getLogger(__name__)


class Command(ZulipBaseCommand):
    help = """Bulk-create users from a CSV file with no header row and
columns (in order): email, full_name, password.

Intended for one-time bulk provisioning (e.g. importing accounts from
an external system) rather than ongoing directory sync. Existing users
(matched by email) are skipped, not updated. Continues past individual
row failures and prints a summary at the end.

No onboarding/account-registered emails are sent for users created
this way (the two calls that would send them are no-ops for the
duration of this command only; nothing else is affected).

Example:
    ./manage.py bulk_create_users_from_csv --realm 2 --csv-file /path/to/users.csv
"""

    @override
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--csv-file",
            required=True,
            help="Path to a CSV file with columns: email,full_name,password (no header row).",
        )
        self.add_realm_args(parser, required=True, help="Realm to add the users to.")

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        realm = self.get_realm(options)
        assert realm is not None

        created = 0
        skipped_existing = 0
        failed: list[tuple[str, str]] = []

        # Bulk-provisioning shouldn't send each user an "account
        # created"/onboarding email; these are the two calls
        # do_create_user makes for that, patched to no-ops for the
        # duration of this command only.
        with (
            patch("zerver.actions.create_user.enqueue_welcome_emails"),
            patch("zerver.actions.create_user.send_account_registered_email"),
            open(options["csv_file"], newline="", encoding="utf-8-sig") as f,
        ):
            reader = csv.reader(f)
            for row_number, row in enumerate(reader, start=1):
                if not row or not row[0].strip():
                    continue
                if len(row) < 3:
                    failed.append((row[0], "row does not have 3 columns"))
                    continue

                email, full_name, password = (value.strip() for value in row[:3])

                try:
                    validate_email(email)
                except ValidationError:
                    failed.append((email, "invalid email address"))
                    continue

                if not full_name:
                    failed.append((email, "empty full_name"))
                    continue
                if not password:
                    failed.append((email, "empty password"))
                    continue

                try:
                    with transaction.atomic():
                        do_create_user(
                            email,
                            password,
                            realm,
                            full_name,
                            acting_user=None,
                        )
                    created += 1
                except IntegrityError:
                    skipped_existing += 1
                except Exception as e:  # noqa: BLE001
                    failed.append((email, f"{type(e).__name__}: {e}"))

                if row_number % 200 == 0:
                    logger.info("Processed %d rows so far...", row_number)

        print(f"Created: {created}")
        print(f"Skipped (already existed): {skipped_existing}")
        print(f"Failed: {len(failed)}")
        for email, reason in failed:
            print(f"  {email}: {reason}")
