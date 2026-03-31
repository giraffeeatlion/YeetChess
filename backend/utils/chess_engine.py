"""
Chess engine utilities for move validation and game state management.
Uses python-chess library for UCI move validation and FEN handling.
"""

import chess
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

GameStatus = Literal["ongoing", "checkmate", "stalemate", "draw", "resigned", "timeout"]


class ChessEngine:
    """Chess move validation and game state management using python-chess."""

    def __init__(self):
        """Initialize the chess engine."""
        pass

    def validate_move(self, current_fen: str, move_uci: str) -> Dict[str, Any]:
        """
        Validate a UCI move against the current board position.

        Args:
            current_fen: Current FEN string of the board
            move_uci: Move in UCI format (e.g., 'e2e4', 'Nf3', 'O-O')

        Returns:
            Dict containing validation result and new state if valid
        """
        try:
            # Create board from FEN
            board = chess.Board(current_fen)

            # Parse UCI move
            try:
                move = chess.Move.from_uci(move_uci)
            except ValueError:
                return {
                    "valid": False,
                    "error": "invalid_uci_format",
                    "message": f"Invalid UCI move format: {move_uci}"
                }

            # Check if move is legal
            if move not in board.legal_moves:
                return {
                    "valid": False,
                    "error": "illegal_move",
                    "message": f"Illegal move: {move_uci}",
                    "legal_moves": [m.uci() for m in board.legal_moves]
                }

            # Make the move to get new state
            board.push(move)

            # Determine game status
            game_status = self._get_game_status(board)

            return {
                "valid": True,
                "move": move_uci,
                "new_fen": board.fen(),
                "game_status": game_status,
                "is_check": board.is_check(),
                "is_checkmate": board.is_checkmate(),
                "is_stalemate": board.is_stalemate(),
                "is_insufficient_material": board.is_insufficient_material(),
                "halfmove_clock": board.halfmove_clock,
                "fullmove_number": board.fullmove_number
            }

        except Exception as e:
            logger.error(f"Error validating move {move_uci} on FEN {current_fen}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": f"Move validation failed: {str(e)}"
            }

    def get_game_status(self, fen: str) -> GameStatus:
        """
        Get the current game status from FEN.

        Args:
            fen: FEN string of the current position

        Returns:
            Game status string
        """
        try:
            board = chess.Board(fen)
            return self._get_game_status(board)
        except Exception as e:
            logger.error(f"Error getting game status from FEN {fen}: {e}")
            return "ongoing"

    def _get_game_status(self, board: chess.Board) -> GameStatus:
        """Determine game status from chess board."""
        if board.is_checkmate():
            return "checkmate"
        elif board.is_stalemate():
            return "stalemate"
        elif board.is_insufficient_material():
            return "draw"
        elif board.can_claim_draw():
            return "draw"
        else:
            return "ongoing"

    def get_legal_moves(self, fen: str) -> list[str]:
        """
        Get all legal moves in UCI format for the current position.

        Args:
            fen: Current FEN string

        Returns:
            List of legal moves in UCI format
        """
        try:
            board = chess.Board(fen)
            return [move.uci() for move in board.legal_moves]
        except Exception as e:
            logger.error(f"Error getting legal moves for FEN {fen}: {e}")
            return []

    def is_game_over(self, fen: str) -> bool:
        """
        Check if the game is over (checkmate, stalemate, or draw).

        Args:
            fen: Current FEN string

        Returns:
            True if game is over, False otherwise
        """
        status = self.get_game_status(fen)
        return status in ["checkmate", "stalemate", "draw"]

    def get_board_info(self, fen: str) -> Dict[str, Any]:
        """
        Get comprehensive board information.

        Args:
            fen: Current FEN string

        Returns:
            Dictionary with board information
        """
        try:
            board = chess.Board(fen)

            return {
                "fen": fen,
                "turn": "white" if board.turn == chess.WHITE else "black",
                "is_check": board.is_check(),
                "is_checkmate": board.is_checkmate(),
                "is_stalemate": board.is_stalemate(),
                "is_insufficient_material": board.is_insufficient_material(),
                "can_claim_draw": board.can_claim_draw(),
                "halfmove_clock": board.halfmove_clock,
                "fullmove_number": board.fullmove_number,
                "legal_moves_count": len(list(board.legal_moves)),
                "game_status": self._get_game_status(board)
            }
        except Exception as e:
            logger.error(f"Error getting board info for FEN {fen}: {e}")
            return {"error": str(e)}


# Global chess engine instance
chess_engine = ChessEngine()