# Running the Core Engine (Console)

This is a minimal, no-network console harness to validate the core state machine.

## Requirements
- Python 3.10+

## Run
```powershell
python -m app.console_runner
```

Modes:
```powershell
python -m app.console_runner scripted
python -m app.console_runner random
python -m app.console_runner interactive
```

## What to Expect
- A single demo hand runs with scripted actions.
- The console prints state snapshots after each action.

## Next Steps
- Add stronger testing (multi-hand loops, edge-case scripts).
- Add side pots and better showdown handling.
- Connect the engine to FastAPI + WebSocket.

## Minimal WebSocket Server
```powershell
uvicorn app.main:app --reload
```

Open the UI:
```
http://localhost:8000/
```

Use the Ready button on the page; the game starts only when all players are ready, and each new hand requires ready again.

Client join message:
```json
{"type": "join", "data": {"player_id": "p1", "name": "Alice"}}
```

Action message:
```json
{"type": "action", "data": {"action": "call", "amount": 0}}
```

Add an AI player (HTTP):
```json
POST /ai
{"player_id": "ai_1", "name": "DealerBot", "chips": 200}
```

Server messages include `schema_version`, `room_id`, `msg_id`, `seq`, and `ts` fields.
