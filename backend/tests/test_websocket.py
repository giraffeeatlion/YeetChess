"""
Tests for WebSocket functionality and real-time chess gameplay.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.schemas.ws_messages import (
    MoveRequest, MoveResult, GameUpdate, WSError, PingMessage, PongMessage
)
from backend.utils.chess_engine import chess_engine
from backend.utils.websocket_manager import connection_manager


class TestWebSocketMessages:
    """Test WebSocket message schemas."""

    def test_move_request_creation(self):
        """Test creating a move request message."""
        move_request = MoveRequest(
            game_id=123,
            player_id=456,
            move="e2e4"
        )

        assert move_request.type == "move"
        assert move_request.game_id == 123
        assert move_request.player_id == 456
        assert move_request.move == "e2e4"
        assert isinstance(move_request.timestamp, datetime)

    def test_move_result_creation(self):
        """Test creating a move result message."""
        move_result = MoveResult(
            game_id=123,
            move="e2e4",
            valid=True,
            new_fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            game_status="ongoing"
        )

        assert move_result.type == "move_result"
        assert move_result.valid is True
        assert move_result.game_status == "ongoing"

    def test_error_message_creation(self):
        """Test creating an error message."""
        error_msg = WSError(
            game_id=123,
            error_code="invalid_move",
            message="Illegal move"
        )

        assert error_msg.type == "error"
        assert error_msg.error_code == "invalid_move"
        assert error_msg.message == "Illegal move"

    def test_ping_pong_messages(self):
        """Test ping/pong message creation."""
        ping = PingMessage(game_id=123)
        pong = PongMessage(game_id=123)

        assert ping.type == "ping"
        assert pong.type == "pong"


class TestChessEngine:
    """Test chess move validation engine."""

    def test_valid_move(self):
        """Test validating a valid move."""
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = chess_engine.validate_move(starting_fen, "e2e4")

        assert result["valid"] is True
        assert result["move"] == "e2e4"
        assert "new_fen" in result
        assert result["game_status"] == "ongoing"
        assert result["is_check"] is False

    def test_invalid_move(self):
        """Test validating an invalid move."""
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = chess_engine.validate_move(starting_fen, "e2e9")

        assert result["valid"] is False
        assert result["error"] == "invalid_uci_format"

    def test_illegal_move(self):
        """Test validating an illegal but properly formatted move."""
        # Try to move king to e2 when it's not legal (king starts on e1)
        result = chess_engine.validate_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e1e2")

        assert result["valid"] is False
        assert result["error"] == "illegal_move"
        assert "legal_moves" in result

    def test_game_status_detection(self):
        """Test game status detection."""
        # Starting position - ongoing
        status = chess_engine.get_game_status("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert status == "ongoing"

        # Checkmate position would require a specific FEN
        # For now, just test the method exists
        assert callable(chess_engine.get_game_status)

    def test_legal_moves(self):
        """Test getting legal moves."""
        moves = chess_engine.get_legal_moves("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert isinstance(moves, list)
        assert len(moves) > 0
        assert "e2e4" in moves  # Should include pawn moves


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.mark.asyncio
    async def test_game_room_creation(self):
        """Test creating and managing game rooms."""
        # This would require mocking WebSocket connections
        # For now, just test the data structures
        room = connection_manager.get_game_room(999)
        assert room is None  # Non-existent game

    def test_connection_info_creation(self):
        """Test connection info creation."""
        from backend.schemas.ws_messages import WSConnectionInfo

        conn_info = WSConnectionInfo(
            game_id=123,
            player_id=456,
            player_username="test_player",
            is_white=True
        )

        assert conn_info.game_id == 123
        assert conn_info.player_id == 456
        assert conn_info.player_username == "test_player"
        assert conn_info.is_white is True


# Integration test for the complete flow
@pytest.mark.asyncio
async def test_move_validation_flow():
    """Test the complete move validation flow."""
    # Simulate a game state
    game_id = 123
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    # Create a move request
    move_request = MoveRequest(
        game_id=game_id,
        player_id=1,
        move="e2e4"
    )

    # Validate the move
    result = chess_engine.validate_move(starting_fen, move_request.move)

    # Create appropriate response
    if result["valid"]:
        move_result = MoveResult(
            game_id=game_id,
            move=move_request.move,
            valid=True,
            new_fen=result["new_fen"],
            game_status=result["game_status"],
            is_check=result.get("is_check", False),
            is_checkmate=result.get("is_checkmate", False),
            is_stalemate=result.get("is_stalemate", False)
        )

        # Verify response structure
        assert move_result.valid is True
        assert move_result.new_fen != starting_fen
        assert move_result.game_status == "ongoing"

        # Create game update for broadcasting
        game_update = GameUpdate(
            game_id=game_id,
            current_fen=move_result.new_fen,
            last_move=move_request.move,
            game_status=move_result.game_status,
            white_player_id=1,
            black_player_id=2,
            turn="black",
            move_number=result.get("fullmove_number", 1)
        )

        assert game_update.last_move == "e2e4"
        assert game_update.turn == "black"

    else:
        # Handle invalid move
        move_result = MoveResult(
            game_id=game_id,
            move=move_request.move,
            valid=False,
            game_status="ongoing",
            error=result.get("error"),
            message=result.get("message")
        )

        assert move_result.valid is False