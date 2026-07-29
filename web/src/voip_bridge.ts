// Bridges the "Add voice call" button to the desktop wrapper app's
// local MicroSIP integration. First step only: toggles the MicroSIP
// window open/closed. Populating the dialed number and pulling user
// contact info are follow-up work once that spec is finalized.
const MICROSIP_BRIDGE_TOGGLE_URL = "http://127.0.0.1:47810/toggle";

export function toggle_microsip_window(): void {
    void fetch(MICROSIP_BRIDGE_TOGGLE_URL).catch(() => {
        // The desktop wrapper's local bridge isn't running (e.g. when
        // testing in a plain browser rather than the wrapper app) --
        // there's nothing else to do here.
    });
}
