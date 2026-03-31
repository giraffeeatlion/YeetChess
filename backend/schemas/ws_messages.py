"""
Pydantic schemas for WebSocket messages in real-time chess games.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


# Message Types
MessageType = Literal[
    "move",           # Player makes a move
    "move_result",    # Server response to move attempt
    "game_update",    # Game state broadcast to all players
    "game_state",     # Complete game state update
    "bot_move",       # Bot makes a move
    "calculate_move", # Request bot to calculate move
    "error",          # Error message
    "ping",           # Connection health check
    "pong"            # Connection health response
]

GameStatus = Literal["ongoing", "checkmate", "stalemate", "draw", "resigned", "timeout"]


# Base message schema
class WSMessage(BaseModel):
    """Base WebSocket message with common fields."""
    type: MessageType
    game_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


# Player move request
class MoveRequest(WSMessage):
    """Player move request message."""
    type: Literal["move"] = "move"
    player_id: int
    move: str = Field(..., description="Move in UCI format (e.g., 'e2e4', 'Nf3', 'O-O')")


# Move validation result
class MoveResult(WSMessage):
    """Server response to move validation."""
    type: Literal["move_result"] = "move_result"
    move: str
    valid: bool
    new_fen: Optional[str] = None
    game_status: GameStatus
    error: Optional[str] = None
    message: Optional[str] = None
    is_check: Optional[bool] = None
    is_checkmate: Optional[bool] = None
    is_stalemate: Optional[bool] = None


# Game state update (broadcast to all players)
class GameUpdate(WSMessage):
    """Game state update broadcast."""
    type: Literal["game_update"] = "game_update"
    current_fen: str
    last_move: Optional[str] = None
    game_status: GameStatus
    white_player_id: Optional[int] = None
    black_player_id: Optional[int] = None
    turn: Literal["white", "black"]
    move_number: int


# Complete game state
class GameState(WSMessage):
    """Complete game state information."""
    type: Literal["game_state"] = "game_state"
    white_player: Optional[Dict[str, Any]] = None
    black_player: Optional[Dict[str, Any]] = None
    current_fen: str
    pgn: str
    status: GameStatus
    created_at: datetime
    updated_at: datetime


# Bot move calculation request
class CalculateMoveRequest(WSMessage):
    """Request for bot to calculate a move."""
    type: Literal["calculate_move"] = "calculate_move"
    current_fen: str
    bot_level: str = Field(default="intermediate", description="Bot difficulty level")
    time_limit_ms: int = Field(default=5000, description="Time limit in milliseconds")


# Bot move response
class BotMove(WSMessage):
    """Bot move response."""
    type: Literal["bot_move"] = "bot_move"
    move: str
    confidence: float = Field(ge=0.0, le=1.0, description="Move confidence score")


# Error message
class WSError(WSMessage):
    """Error message."""
    type: Literal["error"] = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Connection health check
class PingMessage(WSMessage):
    """Connection health check."""
    type: Literal["ping"] = "ping"


class PongMessage(WSMessage):
    """Connection health response."""
    type: Literal["pong"] = "pong"


# Union type for all possible messages
WSMessageUnion = (
    MoveRequest | MoveResult | GameUpdate | GameState |
    CalculateMoveRequest | BotMove | WSError | PingMessage | PongMessage
)


# Connection info
class WSConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    game_id: int
    player_id: int
    player_username: str
    is_white: bool
    connected_at: datetime = Field(default_factory=lambda: datetime.now())


# Game room info
class GameRoom(BaseModel):
    """Information about a game room with connected players."""
    game_id: int
    white_connection: Optional[WSConnectionInfo] = None
    black_connection: Optional[WSConnectionInfo] = None
    spectators: list[WSConnectionInfo] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    @property
    def player_count(self) -> int:
        """Number of connected players."""
        count = 0
        if self.white_connection:
            count += 1
        if self.black_connection:
            count += 1
        return count

    @property
    def total_connections(self) -> int:
        """Total number of connections (players + spectators)."""
        return self.player_count + len(self.spectators)