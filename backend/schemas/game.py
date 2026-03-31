"""
Game Pydantic Schemas
Request/response models for game-related endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class GameCreate(BaseModel):
    """Schema for creating a new game"""
    opponent_type: str = Field(..., pattern="^(random|bot)$")


class GameResponse(BaseModel):
    """Schema for game response"""
    id: int
    white_id: int
    black_id: int
    current_fen: str
    pgn: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    """Schema for listing games"""
    games: list[GameResponse]
    total: int
