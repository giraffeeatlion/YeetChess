# 🎯 YeetChess WebSocket Message Specification

## Overview
This document defines the exact message format for WebSocket communication between clients (human players and bots) and the YeetChess server for real-time chess gameplay.

## Connection Details
- **Endpoint**: `ws://localhost:8000/ws/game/{game_id}`
- **Authentication**: JWT token in query parameter `?token={jwt_token}`
- **Protocol**: JSON over WebSocket

---

## Message Format

All messages follow this base structure:

```json
{
  "type": "message_type",
  "payload": {
    // type-specific data
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "game_id": 123
}
```

### Common Fields
- `type` (string): Message type identifier
- `payload` (object): Type-specific data
- `timestamp` (ISO 8601 string): When the message was sent
- `game_id` (integer): The game this message relates to

---

## Client → Server Messages

### 1. Move Attempt
**Type**: `"move"`

**Purpose**: Player attempts to make a chess move

**Payload**:
```json
{
  "move": "e2e4",
  "move_format": "uci" | "san" | "algebraic",
  "player_color": "white" | "black"
}
```

**Examples**:
```json
// UCI format (most common for bots)
{
  "type": "move",
  "payload": {
    "move": "e2e4",
    "move_format": "uci",
    "player_color": "white"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "game_id": 123
}

// SAN format (human readable)
{
  "type": "move",
  "payload": {
    "move": "Nf3",
    "move_format": "san",
    "player_color": "white"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "game_id": 123
}
```

### 2. Resign Game
**Type**: `"resign"`

**Purpose**: Player resigns the game

**Payload**:
```json
{
  "reason": "resignation",
  "player_color": "white" | "black"
}
```

### 3. Offer Draw
**Type**: `"draw_offer"`

**Purpose**: Player offers a draw

**Payload**:
```json
{
  "player_color": "white" | "black"
}
```

### 4. Accept Draw
**Type**: `"draw_accept"`

**Purpose**: Player accepts a draw offer

**Payload**:
```json
{
  "player_color": "white" | "black"
}
```

---

## Server → Client Messages

### 1. Move Accepted
**Type**: `"move_accepted"`

**Purpose**: Server confirms a valid move and provides updated game state

**Payload**:
```json
{
  "move": "e2e4",
  "move_format": "uci",
  "previous_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "new_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "pgn": "1. e4",
  "player_color": "white",
  "game_status": "ongoing",
  "is_check": false,
  "is_checkmate": false,
  "is_stalemate": false,
  "legal_moves": ["e7e5", "e7e6", "d7d5", "d7d6", "c7c5", "c7c6", "b7b5", "b7b6", "a7a5", "a7a6", "g8f6", "b8c6", "b8a6", "h7h6", "g7g6", "f7f6", "a6a5", "h6h5", "g6g5", "f6f5", "e6e5", "d6d5", "c6c5", "b6b5"]
}
```

### 2. Move Rejected
**Type**: `"move_rejected"`

**Purpose**: Server rejects an invalid move

**Payload**:
```json
{
  "move": "e2e4",
  "move_format": "uci",
  "reason": "illegal_move",
  "details": "King is in check",
  "player_color": "white",
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "legal_moves": ["e7e5", "e7e6", "d7d5", "d7d6", "c7c5", "c7c6", "b7b5", "b7b6", "a7a5", "a7a6", "g8f6", "b8c6", "b8a6", "h7h6", "g7g6", "f7f6", "a6a5", "h6h5", "g6g5", "f6f5", "e6e5", "d6d5", "c6c5", "b6b5"]
}
```

### 3. Game State Update
**Type**: `"game_state"`

**Purpose**: Server broadcasts current game state (used for synchronization)

**Payload**:
```json
{
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "pgn": "1. e4 e5",
  "status": "ongoing",
  "white_player": {
    "id": 1,
    "username": "alice"
  },
  "black_player": {
    "id": 2,
    "username": "bob"
  },
  "current_turn": "white",
  "is_check": false,
  "is_checkmate": false,
  "is_stalemate": false,
  "legal_moves": ["f1c4", "f1b5", "f1a6", "g1f3", "g1h3", "e4e5", "d2d3", "c2c3", "b2b3", "a2a3", "h2h3", "d1h5", "d1g4", "d1f3", "d1e2", "d1d2", "d1d3", "d1d4", "d1d5", "d1d6", "d1d7", "d1d8", "e1e2"]
}
```

### 4. Game Event
**Type**: `"game_event"`

**Purpose**: Special game events like check, checkmate, draw, resignation

**Payload**:
```json
{
  "event_type": "check" | "checkmate" | "stalemate" | "draw" | "resignation" | "timeout",
  "winner": "white" | "black" | null,
  "reason": "checkmate" | "stalemate" | "agreement" | "resignation" | "timeout",
  "final_fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
  "final_pgn": "1. e4 e5"
}
```

### 5. Opponent Move
**Type**: `"opponent_move"`

**Purpose**: Notify player that opponent made a move

**Payload**:
```json
{
  "move": "e7e5",
  "move_format": "uci",
  "opponent_color": "black",
  "new_fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
  "pgn": "1. e4 e5",
  "is_check": false,
  "is_checkmate": false,
  "is_stalemate": false,
  "legal_moves": ["f1c4", "f1b5", "f1a6", "g1f3", "g1h3", "e4e5", "d2d3", "c2c3", "b2b3", "a2a3", "h2h3", "d1h5", "d1g4", "d1f3", "d1e2", "d1d2", "d1d3", "d1d4", "d1d5", "d1d6", "d1d7", "d1d8", "e1e2"]
}
```

### 6. Error Message
**Type**: `"error"`

**Purpose**: Server error or validation failure

**Payload**:
```json
{
  "error_code": "invalid_move_format" | "not_your_turn" | "game_not_found" | "authentication_failed",
  "message": "Human readable error message",
  "details": {
    // Additional error context
  }
}
```

---

## Move Format Specifications

### UCI Format (Universal Chess Interface)
- Most common for bots and engines
- Format: `[from_square][to_square][promotion_piece]`
- Examples: `e2e4`, `g1f3`, `e7e8q` (pawn promotion to queen)
- Always unambiguous, no need for context

### SAN Format (Standard Algebraic Notation)
- Human readable format
- Examples: `e4`, `Nf3`, `O-O`, `Qxd5+`
- Requires current position context to resolve ambiguities

### Algebraic Format
- Long form of SAN
- Examples: `e2-e4`, `Ng1-f3`

---

## Bot Integration Guidelines

### For Bot Developers:
1. **Connect**: `ws://localhost:8000/ws/game/{game_id}?token={jwt_token}`
2. **Listen**: Subscribe to messages with your player color
3. **Move**: Send moves in UCI format for maximum compatibility
4. **Handle**: Process `game_state`, `opponent_move`, and `move_rejected` messages
5. **Legal Moves**: Use the `legal_moves` array to validate your engine's suggestions

### Bot Message Flow:
```
Bot Connects → Receives game_state → Calculates move → Sends move message →
Receives move_accepted or move_rejected → Waits for opponent_move → Repeat
```

---

## Implementation Notes

### Server Responsibilities:
- Validate JWT on WebSocket connection
- Parse and validate move formats
- Use python-chess for move legality checking
- Update database and publish to Redis
- Broadcast state changes to all connected clients

### Client Responsibilities:
- Maintain connection and handle reconnections
- Parse incoming messages and update UI/game state
- Send properly formatted move attempts
- Handle errors gracefully

### Error Handling:
- Invalid moves: Return `move_rejected` with reason and legal alternatives
- Network issues: Clients should implement reconnection logic
- Authentication failures: Immediate connection closure

---

## Testing Examples

### Valid Move Sequence:
```json
// Client sends move
{"type": "move", "payload": {"move": "e2e4", "move_format": "uci", "player_color": "white"}}

// Server responds with acceptance
{"type": "move_accepted", "payload": {"move": "e2e4", "new_fen": "...", "legal_moves": [...]}}
```

### Invalid Move Sequence:
```json
// Client sends invalid move
{"type": "move", "payload": {"move": "e2e9", "move_format": "uci", "player_color": "white"}}

// Server responds with rejection
{"type": "move_rejected", "payload": {"move": "e2e9", "reason": "illegal_move", "legal_moves": [...]}}
```

This specification ensures consistent communication between human players, bots, and the server for reliable real-time chess gameplay.</content>
<parameter name="filePath">/home/lalithkommasani/YeetChess/WEBSOCKET_SPEC.md