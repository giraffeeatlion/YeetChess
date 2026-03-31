"""
User ORM Model
SQLAlchemy model for the users table.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    """User model representing a registered player"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    white_games = relationship("Game", foreign_keys="Game.white_id", back_populates="white_player")
    black_games = relationship("Game", foreign_keys="Game.black_id", back_populates="black_player")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
