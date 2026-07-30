import $ from "jquery";

// Bridges the navbar call-toggle button to the desktop wrapper app's
// local MicroSIP integration. Lives in the navbar (not compose)
// because dialing is driven by whichever contact is selected in the
// left sidebar, not by what's being composed. First step only:
// toggles the MicroSIP window open/closed. Populating the dialed
// number and pulling user contact info are follow-up work once that
// spec is finalized.
const MICROSIP_BRIDGE_TOGGLE_URL = "http://127.0.0.1:47810/toggle";

export async function toggle_microsip_window(): Promise<void> {
    try {
        await fetch(MICROSIP_BRIDGE_TOGGLE_URL);
    } catch {
        // The desktop wrapper's local bridge isn't running (e.g. when
        // testing in a plain browser rather than the wrapper app) --
        // there's nothing else to do here.
    }
}

export function initialize(): void {
    $("body").on("click", "#navbar-voip-toggle", (e) => {
        e.preventDefault();
        e.stopPropagation();
        void toggle_microsip_window();
    });
}
