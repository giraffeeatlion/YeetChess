"""
WebSocket API endpoints for real-time chess gameplay.
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
import json

from backend.database import get_db
from backend.models.user import User
from backend.models.game import Game
from backend.utils.security import verify_token
from backend.utils.chess_engine import chess_engine
from backend.utils.redis_client import redis_client
from backend.utils.websocket_manager import connection_manager
from backend.schemas.ws_messages import (
    MoveRequest, MoveResult, GameUpdate, WSError, PingMessage, PongMessage,
    GameStatus
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_ws(token: str = Query(..., alias="token")) -> User:
    """
    WebSocket dependency to authenticate user from JWT token.

    Args:
        token: JWT token from query parameter

    Returns:
        Authenticated user

    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_token(token, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # For WebSocket, we can't inject DB session here
    # We'll need to get user info from the connection manager
    # This is a simplified version - in production you'd want proper user lookup
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Create a minimal user object for WebSocket context
    # In production, you'd fetch from DB
    class WSUser:
        def __init__(self, id: int, username: str):
            self.id = id
            self.username = username

    return WSUser(id=int(user_id), username=f"user_{user_id}")


@router.websocket("/ws/game/{game_id}")
async def game_websocket(
    websocket: WebSocket,
    game_id: int,
    token: str = Query(..., alias="token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chess gameplay.

    Args:
        websocket: WebSocket connection
        game_id: Game ID from URL path
        token: JWT token from query parameter
        db: Database session
    """
    # Authenticate user
    try:
        user = await get_current_user_ws(token)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return

    # Get game from database
    game = await db.get(Game, game_id)
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return

    # Determine if user is white or black player
    is_white = game.white_id == user.id
    is_black = game.black_id == user.id

    if not is_white and not is_black:
        await websocket.close(code=4003, reason="You are not a player in this game")
        return

    # Connect to game room
    connected = await connection_manager.connect(
        websocket=websocket,
        game_id=game_id,
        player_id=user.id,
        player_username=user.username,
        is_white=is_white
    )

    if not connected:
        await websocket.close(code=4000, reason="Failed to connect to game")
        return

    logger.info(f"Player {user.username} connected to game {game_id}")

    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_json()
                await handle_websocket_message(websocket, game_id, user.id, data, db)
            except json.JSONDecodeError:
                await connection_manager.send_to_player(
                    websocket,
                    WSError(
                        game_id=game_id,
                        error_code="invalid_json",
                        message="Invalid JSON format"
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"Player {user.username} disconnected from game {game_id}")
    except Exception as e:
        logger.error(f"WebSocket error for game {game_id}, player {user.id}: {e}")
    finally:
        # Clean up connection
        await connection_manager.disconnect(websocket)


async def handle_websocket_message(
    websocket: WebSocket,
    game_id: int,
    player_id: int,
    data: dict,
    db: AsyncSession
) -> None:
    """
    Handle incoming WebSocket messages.

    Args:
        websocket: WebSocket connection
        game_id: Game ID
        player_id: Player ID who sent the message
        data: Message data
        db: Database session
    """
    try:
        message_type = data.get("type")

        if message_type == "move":
            await handle_move_request(websocket, game_id, player_id, data, db)

        elif message_type == "ping":
            # Respond to ping with pong
            await connection_manager.send_to_player(
                websocket,
                PongMessage(game_id=game_id)
            )

        else:
            await connection_manager.send_to_player(
                websocket,
                WSError(
                    game_id=game_id,
                    error_code="unknown_message_type",
                    message=f"Unknown message type: {message_type}"
                )
            )

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await connection_manager.send_to_player(
            websocket,
            WSError(
                game_id=game_id,
                error_code="internal_error",
                message="Internal server error"
            )
        )


async def handle_move_request(
    websocket: WebSocket,
    game_id: int,
    player_id: int,
    data: dict,
    db: AsyncSession
) -> None:
    """
    Handle a move request from a player.

    Args:
        websocket: WebSocket connection
        game_id: Game ID
        player_id: Player ID making the move
        data: Move request data
        db: Database session
    """
    try:
        # Parse move request
        move_request = MoveRequest(**data)

        # Get current game state
        game = await db.get(Game, game_id)
        if not game:
            await connection_manager.send_to_player(
                websocket,
                WSError(
                    game_id=game_id,
                    error_code="game_not_found",
                    message="Game not found"
                )
            )
            return

        # Check if it's player's turn
        current_turn_white = game.current_fen.split()[1] == 'w'
        is_player_white = game.white_id == player_id
        is_player_black = game.black_id == player_id

        if (current_turn_white and not is_player_white) or (not current_turn_white and not is_player_black):
            await connection_manager.send_to_player(
                websocket,
                MoveResult(
                    game_id=game_id,
                    move=move_request.move,
                    valid=False,
                    game_status=game.status,
                    error="not_your_turn",
                    message="It's not your turn to move"
                )
            )
            return

        # Validate move using chess engine
        validation_result = chess_engine.validate_move(game.current_fen, move_request.move)

        if validation_result["valid"]:
            # Move is valid - update game state
            game.current_fen = validation_result["new_fen"]
            game.status = validation_result["game_status"]

            # Update PGN (simplified - in production you'd use python-chess PGN handling)
            if game.pgn:
                game.pgn += f" {move_request.move}"
            else:
                game.pgn = move_request.move

            # Save to database
            await db.commit()

            # Send success response to player
            move_result = MoveResult(
                game_id=game_id,
                move=move_request.move,
                valid=True,
                new_fen=game.current_fen,
                game_status=game.status,
                is_check=validation_result.get("is_check", False),
                is_checkmate=validation_result.get("is_checkmate", False),
                is_stalemate=validation_result.get("is_stalemate", False)
            )
            await connection_manager.send_to_player(websocket, move_result)

            # Broadcast game update to all players
            game_update = GameUpdate(
                game_id=game_id,
                current_fen=game.current_fen,
                last_move=move_request.move,
                game_status=game.status,
                white_player_id=game.white_id,
                black_player_id=game.black_id,
                turn="black" if current_turn_white else "white",
                move_number=validation_result.get("fullmove_number", 1)
            )
            await connection_manager.broadcast_to_game(game_id, game_update, exclude_websocket=websocket)

            # If it's a bot's turn, request bot move
            if game.black_id is None or game.white_id is None:  # Bot game
                if game.status == "ongoing":
                    await redis_client.publish_bot_request(
                        game_id=game_id,
                        fen=game.current_fen,
                        bot_level="intermediate"
                    )

        else:
            # Move is invalid
            move_result = MoveResult(
                game_id=game_id,
                move=move_request.move,
                valid=False,
                game_status=game.status,
                error=validation_result.get("error", "invalid_move"),
                message=validation_result.get("message", "Invalid move")
            )
            await connection_manager.send_to_player(websocket, move_result)

    except Exception as e:
        logger.error(f"Error handling move request: {e}")
        await connection_manager.send_to_player(
            websocket,
            WSError(
                game_id=game_id,
                error_code="move_processing_error",
                message="Error processing move"
            )
        )