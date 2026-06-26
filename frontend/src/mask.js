export const MASK = "•••";

// A `fill` value can be a password or other secret the user asked the agent to
// type; never render it. Other actions' values (e.g. a `press` key like "Enter")
// are not sensitive and pass through. Display-layer only — the event payload is
// unchanged; this just keeps secrets off the screen.
export function maskArgs(args) {
  if (args && args.action === "fill" && args.value != null) {
    return { ...args, value: MASK };
  }
  return args;
}
