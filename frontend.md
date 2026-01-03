# Frontend Plan (Vue 3 CDN)

## Goals
- Migrate the current static HTML/JS UI to Vue 3 using CDN (no build tooling).
- Keep the existing layout and styles, only replace imperative DOM updates.
- Preserve the WebSocket and HTTP protocol already implemented by the backend.

## Scope
- Replace `app/static/index.html` inline JS with Vue 3 app + components.
- Keep CSS largely unchanged.
- Do not change backend logic or message formats in this pass.

## Tasks

### 1) Entry Setup
- Add Vue 3 CDN script tag in `app/static/index.html`.
- Create a `#app` root container.
- Move existing DOM markup under `#app`.

### 2) App State
Define top-level reactive state:
- `socket`, `connected`
- `lastState`
- `logItems`
- `playerId`, `playerName`
- `aiId`, `aiName`
- `raiseAmount`

Derived/computed:
- `me`, `isMyTurn`, `toCall`, `minRaise`, `maxRaise`
- `handInProgress`, `canAct`, `canRemoveAi`

### 3) Components (single-file, in-page)
- `ControlPanel`: connect/ready/add AI.
- `TableMeta`: stage/pot/current player.
- `CommunityCards`: render 5 community cards.
- `Seats`: table seat layout.
- `PlayersList`: seated list + waiting list.
- `ActionBar`: action buttons + raise input.
- `LogPanel`: system/error logs.

### 4) WebSocket + HTTP
- WebSocket: connect, join, message dispatch, close.
- HTTP: `/ai` add, `/ai/remove` remove.
- Message handling:
  - `game_update`: update `lastState`.
  - `system`: append formatted log entry.
  - `error`: append formatted log entry.

### 5) UI Logic (match current behavior)
- Ready button state rules: `awaiting_ready`, `handInProgress`, `me.seated`.
- Action button enable/disable based on `canAct`, `toCall`.
- Waiting list uses `player.seated === false`.
- System log displays `player_joined` with `waiting/seated`.

### 6) Reuse Styles
- Keep the existing CSS as-is.
- Adjust only if Vue structure requires minimal changes.

### 7) Manual Checks
- Connect/disconnect.
- Ready/unready.
- Add/remove AI.
- Action flow (fold/check/call/raise/all-in).
- Waiting queue during active hand.
- System/error log formatting.
