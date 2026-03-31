"""
WebSocket connection manager for real-time chess games.
Manages game rooms, player connections, and message broadcasting.
"""

import asyncio
import logging
from typing import Dict, Optional, Set
from fastapi import WebSocket
import json
from datetime import datetime, timezone

from backend.schemas.ws_messages import (
    WSConnectionInfo, GameRoom, WSMessageUnion,
    MoveRequest, MoveResult, GameUpdate, WSError, PingMessage, PongMessage
)
from backend.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for chess games."""

    def __init__(self):
        # game_id -> GameRoom
        self.game_rooms: Dict[int, GameRoom] = {}
        # websocket -> connection_info
        self.connections: Dict[WebSocket, WSConnectionInfo] = {}
        # game_id -> set of active websockets
        self.active_games: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: int, player_id: int,
                     player_username: str, is_white: bool) -> bool:
        """
        Connect a player to a game room.

        Args:
            websocket: WebSocket connection
            game_id: Game ID
            player_id: Player ID
            player_username: Player username
            is_white: Whether player is white

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await websocket.accept()

            # Create connection info
            connection_info = WSConnectionInfo(
                game_id=game_id,
                player_id=player_id,
                player_username=player_username,
                is_white=is_white
            )

            # Get or create game room
            if game_id not in self.game_rooms:
                self.game_rooms[game_id] = GameRoom(game_id=game_id)
                self.active_games[game_id] = set()

            room = self.game_rooms[game_id]

            # Assign player to correct position
            if is_white and not room.white_connection:
                room.white_connection = connection_info
            elif not is_white and not room.black_connection:
                room.black_connection = connection_info
            else:
                # Add as spectator
                room.spectators.append(connection_info)

            # Store connection mapping
            self.connections[websocket] = connection_info
            self.active_games[game_id].add(websocket)

            # Subscribe to Redis channel for this game
            await redis_client.subscribe_to_game(game_id, self._handle_redis_message)

            logger.info(f"Player {player_username} connected to game {game_id} as {'white' if is_white else 'black'}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect player {player_id} to game {game_id}: {e}")
            return False

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a player from their game room.

        Args:
            websocket: WebSocket connection to disconnect
        """
        if websocket not in self.connections:
            return

        connection_info = self.connections[websocket]
        game_id = connection_info.game_id

        # Remove from game room
        if game_id in self.game_rooms:
            room = self.game_rooms[game_id]

            # Remove from appropriate position
            if room.white_connection and room.white_connection.player_id == connection_info.player_id:
                room.white_connection = None
            elif room.black_connection and room.black_connection.player_id == connection_info.player_id:
                room.black_connection = None
            else:
                # Remove from spectators
                room.spectators = [s for s in room.spectators if s.player_id != connection_info.player_id]

            # Remove from active games
            if game_id in self.active_games:
                self.active_games[game_id].discard(websocket)

                # Clean up empty game rooms
                if not self.active_games[game_id]:
                    del self.active_games[game_id]
                    del self.game_rooms[game_id]
                    # Unsubscribe from Redis
                    await redis_client.unsubscribe_from_game(game_id)

        # Remove connection mapping
        del self.connections[websocket]

        logger.info(f"Player {connection_info.player_username} disconnected from game {game_id}")

    async def broadcast_to_game(self, game_id: int, message: WSMessageUnion,
                               exclude_websocket: Optional[WebSocket] = None) -> None:
        """
        Broadcast a message to all players in a game.

        Args:
            game_id: Game ID to broadcast to
            message: Message to broadcast
            exclude_websocket: WebSocket to exclude from broadcast (optional)
        """
        if game_id not in self.active_games:
            return

        # Convert message to dict
        message_dict = message.model_dump()

        # Broadcast to all connections in the game
        disconnected = []
        for websocket in self.active_games[game_id]:
            if websocket == exclude_websocket:
                continue

            try:
                await websocket.send_json(message_dict)
            except Exception as e:
                logger.error(f"Failed to send message to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def send_to_player(self, websocket: WebSocket, message: WSMessageUnion) -> bool:
        """
        Send a message to a specific player.

        Args:
            websocket: Target WebSocket connection
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message_dict = message.model_dump()
            await websocket.send_json(message_dict)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to websocket: {e}")
            await self.disconnect(websocket)
            return False

    async def _handle_redis_message(self, message: Dict) -> None:
        """
        Handle messages received from Redis Pub/Sub.

        Args:
            message: Message from Redis
        """
        try:
            game_id = message.get("game_id")
            if not game_id or game_id not in self.active_games:
                return

            # Convert message type to appropriate schema
            message_type = message.get("type")

            if message_type == "game_update":
                # Broadcast game updates to all players
                game_update = GameUpdate(**message)
                await self.broadcast_to_game(game_id, game_update)

            elif message_type == "bot_move":
                # Handle bot moves
                from backend.schemas.ws_messages import BotMove
                bot_move = BotMove(**message)
                await self.broadcast_to_game(game_id, bot_move)

            # Add more message type handlers as needed

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

    def get_game_room(self, game_id: int) -> Optional[GameRoom]:
        """
        Get information about a game room.

        Args:
            game_id: Game ID

        Returns:
            GameRoom object or None if game doesn't exist
        """
        return self.game_rooms.get(game_id)

    def get_player_connection(self, websocket: WebSocket) -> Optional[WSConnectionInfo]:
        """
        Get connection info for a WebSocket.

        Args:
            websocket: WebSocket connection

        Returns:
            Connection info or None
        """
        return self.connections.get(websocket)

    def is_player_connected(self, game_id: int, player_id: int) -> bool:
        """
        Check if a specific player is connected to a game.

        Args:
            game_id: Game ID
            player_id: Player ID

        Returns:
            True if player is connected, False otherwise
        """
        room = self.get_game_room(game_id)
        if not room:
            return False

        if room.white_connection and room.white_connection.player_id == player_id:
            return True
        if room.black_connection and room.black_connection.player_id == player_id:
            return True

        return any(s.player_id == player_id for s in room.spectators)


# Global connection manager instance
connection_manager = ConnectionManager()