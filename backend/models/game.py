"""
Game ORM Model
SQLAlchemy model for the games table.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class Game(Base):
    """Game model representing a chess game between two players"""
    
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    white_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    black_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_fen = Column(
        String(500),
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        nullable=False
    )
    pgn = Column(String, default="")
    status = Column(String(50), default="ongoing", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    white_player = relationship("User", foreign_keys=[white_id], back_populates="white_games")
    black_player = relationship("User", foreign_keys=[black_id], back_populates="black_games")
    
    def __repr__(self):
        return f"<Game(id={self.id}, white={self.white_id}, black={self.black_id}, status={self.status})>"
