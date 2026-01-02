# Simple Multi-Player AI Texas Hold'em Design (SimpleHoldem-AI)

## 1. Vision
Build a lightweight, easy-to-deploy multi-player online Texas Hold'em game.
- **Core feature**: Human players compete with LLM-driven AI players.
- **Architecture philosophy**: Monolith + in-memory state. Prioritize development speed and code readability, ideal for a solo developer MVP.

## 2. Tech Stack (Python Full-Stack)
- **Backend framework**: `FastAPI` (HTTP + WebSocket, async by default).
- **Network protocol**: `WebSocket` (real-time game communication).
- **Storage**:
  - **Hot data**: Python **memory** (global `Dict`) stores rooms and game state; fastest, no external dependency.
  - **Persistence (optional)**: `SQLite` only for basic config or user credentials (can be skipped for MVP).
- **AI integration**: `OpenAI SDK` (or compatible APIs like DeepSeek/Claude) + `AsyncIO`.
- **Frontend**: HTML5 + Vue.js/React (CDN-based, no build tooling).

## 3. System Architecture

### 3.1 Modules (Folder Layout)
The backend is a single Python project to avoid microservice complexity.

```text
/app
  |-- main.py            # Entry: start FastAPI, register routes
  |-- models.py          # Data structures: Player, Room, GameState, etc.
  |-- game_engine.py     # Core logic: shuffle/deal, hand eval, pot calc, state machine
  |-- connection_mgr.py  # Network layer: WebSocket connections and broadcast
  `-- ai_agent.py        # AI layer: prompt building and API calls
```

### 3.2 Runtime Diagram (Mermaid)

```mermaid
graph TD
    ClientA[Human Player A] <-->|WebSocket| API[FastAPI Gateway]
    ClientB[Human Player B] <-->|WebSocket| API

    subgraph "Backend Server (single process)"
        API --> Manager[Connection Manager]
        API --> Engine[Game State Machine (in memory)]

        Engine -- AI turn --> AI_Mod[AI Module]
        AI_Mod -- HTTP --> LLM_Cloud[LLM API]
    end

    Manager -- broadcast JSON --> ClientA
    Manager -- broadcast JSON --> ClientB
```

## 4. Core Data Models (In-Memory Objects)
These objects live in memory only; a server restart resets everything.

### 4.1 Room
```python
class Room:
    id: str
    players: List[Player]      # Humans + AI
    deck: List[str]            # Deck (e.g., ['Ah', 'Td'])
    community_cards: List[str] # Community cards
    pot: int                   # Current pot
    current_actor_index: int   # Whose turn (seat index)
    stage: str                 # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN
```

### 4.2 Player
```python
class Player:
    id: str
    is_ai: bool           # Key flag: AI or human
    chips: int            # Remaining chips
    hand: List[str]       # Hole cards ['Ah', 'Kd']
    status: str           # WAITING, PLAYING, FOLDED, ALLIN
    websocket: WebSocket  # Only humans have this connection; AI is None
```

## 5. Core Logic Flow
### 5.1 Game Loop (State Machine)
This is the heart of the game, in `game_engine.py`.

1. WaitForAction: server waits for the current player's action.
2. ActionReceived:
   - Human: receive JSON via WebSocket `{"action": "raise", "amount": 100}`.
   - AI: internal trigger, call LLM to get JSON.
3. Validate: check legality (enough chips? is it your turn?).
4. UpdateState: update pot, player chips, betting round state.
5. CheckStageEnd: determine whether the betting round ends.
   - Yes: deal community cards -> move to next stage (e.g., FLOP -> TURN).
   - No: move `current_actor_index` to the next player.
6. Broadcast: push latest `GameState` to all clients.

### 5.2 AI Decision Flow (Critical Path)
When `current_actor_index` points to an `is_ai=True` player:

1. Pause waiting: no WebSocket wait.
2. Build prompt: collect table info (community cards, pot, AI hand, action history).
3. Async call: `await llm_client.chat.completions.create(...)`.
4. Parse & execute: call `engine.process_action()` as if a human clicked a button.
5. Delayed simulation: add `await asyncio.sleep(1)` to simulate thinking time.

### 5.3 Betting Rules and Round Boundaries (MVP Detail)
Keep rules explicit to avoid edge-case bugs in multi-player betting.

- **Blinds and button**:
  - Each hand has a `dealer_index`, `small_blind_index`, `big_blind_index`.
  - Preflop action starts from the player left of big blind; postflop action starts from small blind.
  - Advance dealer each hand to the next active seat.
- **Per-round state**:
  - Track `current_bet` (highest bet this round), `last_raise_size`, and `has_acted` per player.
  - A player is **active** if not folded and has chips or is all-in.
- **Legal actions**:
  - `fold`: always allowed.
  - `check`: allowed only if player's bet equals `current_bet`.
  - `call`: allowed if player's bet < `current_bet`; call amount = `current_bet - player.bet`.
  - `raise`: allowed if player can increase the bet by at least `min_raise`.
  - `allin`: allowed if chips > 0; counts as call or raise depending on amount.
- **Minimum raise**:
  - `min_raise = max(big_blind, last_raise_size)` for the round.
  - If `raise_amount < min_raise`, reject as invalid.
  - If `allin` does not reach `min_raise`, it is treated as a call and does not reopen action.
- **Round end conditions**:
  - The betting round ends when all active non-all-in players have `has_acted = true` and their bets equal `current_bet`.
  - If only one player remains not folded, the hand ends immediately.
- **Stage transitions**:
  - PREFLOP -> FLOP: deal 3 community cards, reset per-round bets and `has_acted`.
  - FLOP -> TURN and TURN -> RIVER: deal 1 card each, reset per-round bets and `has_acted`.
  - RIVER -> SHOWDOWN: evaluate hands, award pot.
- **Showdown (no side pots in MVP)**:
  - If multiple players are all-in, compare only the main pot for now.
  - Split pot equally among tied winners (handle remainder by house rule, e.g., first seat).

## 6. API/Protocol Design
### 6.1 WebSocket Message Format
Client -> Server:

```json
{
  "type": "action",
  "data": {
    "action": "call",  // fold, check, call, raise, allin
    "amount": 0
  }
}
```

Server -> Client (broadcast):

```json
{
  "type": "game_update",
  "data": {
    "stage": "FLOP",
    "pot": 200,
    "community_cards": ["As", "Kd", "2c"],
    "current_player_id": "player_3",
    "seats": [
      {"id": "player_1", "name": "Human", "chips": 900, "bet": 100, "is_active": true},
      {"id": "player_2", "name": "GPT-4", "chips": 1500, "bet": 100, "is_active": true}
    ]
  }
}
```

### 6.2 Protocol Versioning, Ordering, and Errors
Add lightweight metadata to allow evolution and debugging.

**Envelope fields** (recommended):
- `schema_version`: integer (e.g., 1), bump on breaking changes.
- `room_id`: string, explicit routing and debugging.
- `msg_id`: string UUID from sender.
- `seq`: server sequence number for ordering.
- `ts`: server timestamp (ms since epoch) for client reconciliation.

**Error message** (server -> client):
```json
{
  "type": "error",
  "schema_version": 1,
  "room_id": "room_123",
  "msg_id": "srv-9f5c",
  "seq": 42,
  "ts": 1730000000000,
  "data": {
    "code": "INVALID_ACTION",
    "message": "raise below minimum",
    "details": {"min_raise": 50, "current_bet": 100, "player_bet": 100}
  }
}
```

**System message** (server -> client):
```json
{
  "type": "system",
  "schema_version": 1,
  "room_id": "room_123",
  "msg_id": "srv-9f5d",
  "seq": 43,
  "ts": 1730000000100,
  "data": {
    "event": "player_timeout",
    "player_id": "player_3",
    "auto_action": "fold"
  }
}
```

## 7. MVP Roadmap (Suggested Order)
Phase 1: Single-Player Console (The Core)
- Goal: no networking, just Python classes.
- Work: implement shuffle/deal, hand evaluation (suggest `treys`), simple AI (random actions).
- Test: run a full game in the terminal and verify chip math.

Phase 2: Add the Brain (The Brain)
- Goal: make the AI smarter.
- Work: write prompt, integrate OpenAI API.
- Test: play against AI in the terminal; see if it bluffs.

Phase 3: Server Mode (The Server)
- Goal: support multiple connections.
- Work: add FastAPI + WebSocket, wrap core logic from Phase 1.
- Test: connect via Postman or a simple HTML page and see JSON updates.

Phase 4: UI (The Face)
- Goal: playable UI.
- Work: build a simple web page (community cards, hole cards, action buttons).

## 8. Pitfalls to Avoid (Solo Project)
1. No side pots: multiple all-ins are complex. MVP rule: return extra chips to bigger stacks; only main pot is compared.
2. No reconnection: disconnect = fold.
3. No complex auth: entering a room requires only a name; no signup/login/email verification.
4. AI timeout handling: set API timeout to 5 seconds; if AI times out, auto-choose `Check` or `Fold`.
