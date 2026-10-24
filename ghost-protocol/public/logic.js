// Ghost Protocol: Neon Maze — solo game: platform rules-module stub.
export const meta = { game: "ghost-protocol-neon-maze", minPlayers: 1, maxPlayers: 1 };
export function setup() { return {}; }
export function validateAction() { return { ok: true }; }
export function applyAction(state) { return state; }
export function isGameOver() { return { over: false }; }
export function viewFor(state) { return state; }
