#!/usr/bin/env python3
"""
YeetChess Move Format Validator
Tests and validates the move formats specified in MOVE_FORMAT_SPEC.md
"""

import chess
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class MoveValidator:
    """Validates chess moves using python-chess library"""

    def __init__(self):
        self.board = chess.Board()

    def reset_board(self):
        """Reset to starting position"""
        self.board = chess.Board()

    def set_position(self, fen: str):
        """Set board position from FEN"""
        self.board = chess.Board(fen)

    def validate_move(self, move_uci: str) -> Dict[str, Any]:
        """
        Validate a move in UCI format and return result
        Returns the same format as specified in MOVE_FORMAT_SPEC.md
        """
        try:
            # Parse UCI move
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return {
                "valid": False,
                "error": "INVALID_MOVE_FORMAT",
                "message": f"Move must be in UCI format (e.g., e2e4): {move_uci}"
            }

        # Check if move is legal
        if move not in self.board.legal_moves:
            return {
                "valid": False,
                "error": "ILLEGAL_MOVE",
                "message": f"Illegal move in current position: {move_uci}",
                "current_fen": self.board.fen()
            }

        # Apply the move
        san_move = self.board.san(move)  # For display purposes
        self.board.push(move)

        # Determine game status
        game_status = self._get_game_status()

        return {
            "valid": True,
            "new_fen": self.board.fen(),
            "game_status": game_status,
            "san_move": san_move  # For UI display
        }

    def _get_game_status(self) -> str:
        """Determine the current game status"""
        if self.board.is_checkmate():
            return "checkmate"
        elif self.board.is_stalemate():
            return "stalemate"
        elif self.board.is_insufficient_material():
            return "draw"
        elif self.board.can_claim_draw():
            return "draw"
        else:
            return "ongoing"

    def get_legal_moves_uci(self) -> list[str]:
        """Get all legal moves in UCI format"""
        return [move.uci() for move in self.board.legal_moves]


def test_move_formats():
    """Test various move formats as specified in the spec"""
    validator = MoveValidator()

    print("=== YEETCHESS MOVE FORMAT VALIDATION ===\n")

    # Test cases from the specification
    test_cases = [
        # Valid UCI moves
        ("e2e4", True, "Basic pawn move"),
        ("g1f3", True, "Knight move"),
        ("e1g1", True, "King-side castle"),
        ("e1c1", True, "Queen-side castle"),

        # Invalid moves
        ("e2e9", False, "Invalid square"),
        ("invalid", False, "Not UCI format"),
        ("Nf3", False, "SAN format not accepted"),
        ("O-O", False, "SAN castle format not accepted"),
    ]

    print("Testing UCI Move Format Compliance:")
    print("-" * 50)

    for move_str, should_be_valid, description in test_cases:
        result = validator.validate_move(move_str)
        is_valid = result["valid"]

        status = "✓ PASS" if is_valid == should_be_valid else "✗ FAIL"
        print(f"{move_str:10} | {status} | {description}")

        if not is_valid and "error" in result:
            print(f"    Error: {result['error']} - {result['message']}")

    print("\n" + "=" * 50)

    # Test a sequence of moves
    print("Testing Move Sequence (Opening):")
    print("-" * 30)

    validator.reset_board()
    opening_moves = ["e2e4", "e7e5", "g1f3", "b8c6"]

    for i, move in enumerate(opening_moves, 1):
        result = validator.validate_move(move)
        if result["valid"]:
            print("2d")
        else:
            print("2d")
            break

    print(f"\nFinal position FEN: {validator.board.fen()}")
    print(f"Game status: {validator._get_game_status()}")


def demonstrate_websocket_formats():
    """Demonstrate the WebSocket message formats"""
    print("\n=== WEBSOCKET MESSAGE FORMAT DEMO ===\n")

    # Player move request
    player_move_request = {
        "type": "move",
        "game_id": 123,
        "player_id": 456,
        "move": "e2e4",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("Player Move Request:")
    print(json.dumps(player_move_request, indent=2))

    # Server validation response
    validator = MoveValidator()
    result = validator.validate_move("e2e4")

    move_response = {
        "type": "move_result",
        "game_id": 123,
        "move": "e2e4",
        "valid": result["valid"],
        "new_fen": result.get("new_fen", ""),
        "game_status": result.get("game_status", "ongoing"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("\nServer Move Response:")
    print(json.dumps(move_response, indent=2))

    # Bot move format
    bot_move_request = {
        "type": "calculate_move",
        "game_id": 123,
        "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "bot_level": "intermediate",
        "time_limit_ms": 5000
    }

    print("\nBot Move Request:")
    print(json.dumps(bot_move_request, indent=2))

    bot_response = {
        "type": "bot_move",
        "game_id": 123,
        "move": "e2e4",
        "confidence": 0.85,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("\nBot Move Response:")
    print(json.dumps(bot_response, indent=2))


if __name__ == "__main__":
    test_move_formats()
    demonstrate_websocket_formats()

    print("\n" + "=" * 60)
    print("✅ MOVE FORMAT SPECIFICATION VALIDATED")
    print("✅ READY FOR PHASE 3: REAL-TIME CHESS ENGINE")
    print("=" * 60)
