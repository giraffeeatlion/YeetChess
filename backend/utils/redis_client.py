"""
Redis client for Pub/Sub messaging in real-time chess games.
Handles game state broadcasting and bot communication.
"""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for Pub/Sub operations."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscriptions: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def publish_game_update(self, game_id: int, message: Dict[str, Any]) -> bool:
        """
        Publish a game update to the game's Redis channel.

        Args:
            game_id: Game ID
            message: Message to publish

        Returns:
            True if published successfully, False otherwise
        """
        if not self.redis:
            logger.error("Redis not connected")
            return False

        try:
            channel = f"game_{game_id}"
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Convert to JSON
            message_json = json.dumps(message)

            # Publish to channel
            await self.redis.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {message_json}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish game update for game {game_id}: {e}")
            return False

    async def subscribe_to_game(self, game_id: int, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Subscribe to a game's Redis channel.

        Args:
            game_id: Game ID to subscribe to
            callback: Async function to call when messages are received
        """
        if not self.redis:
            logger.error("Redis not connected")
            return

        try:
            channel = f"game_{game_id}"
            self.subscriptions[channel] = callback

            # Create pubsub instance if not exists
            if not self.pubsub:
                self.pubsub = self.redis.pubsub()

            # Subscribe to channel
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to game channel: {channel}")

            # Start listening in background
            asyncio.create_task(self._listen_to_channel(channel))

        except Exception as e:
            logger.error(f"Failed to subscribe to game {game_id}: {e}")

    async def unsubscribe_from_game(self, game_id: int) -> None:
        """
        Unsubscribe from a game's Redis channel.

        Args:
            game_id: Game ID to unsubscribe from
        """
        if not self.pubsub:
            return

        try:
            channel = f"game_{game_id}"
            await self.pubsub.unsubscribe(channel)
            self.subscriptions.pop(channel, None)
            logger.info(f"Unsubscribed from game channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from game {game_id}: {e}")

    async def _listen_to_channel(self, channel: str) -> None:
        """
        Listen to a specific channel and call the callback for messages.

        Args:
            channel: Channel name to listen to
        """
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message" and message["channel"] == channel:
                    try:
                        # Parse JSON message
                        data = json.loads(message["data"])
                        # Call callback
                        callback = self.subscriptions.get(channel)
                        if callback:
                            await callback(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON message on {channel}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message on {channel}: {e}")
        except Exception as e:
            logger.error(f"Error listening to channel {channel}: {e}")

    async def publish_bot_request(self, game_id: int, fen: str, bot_level: str = "intermediate", time_limit_ms: int = 5000) -> bool:
        """
        Publish a bot move calculation request.

        Args:
            game_id: Game ID
            fen: Current FEN position
            bot_level: Difficulty level for the bot
            time_limit_ms: Time limit for move calculation

        Returns:
            True if published successfully
        """
        message = {
            "type": "calculate_move",
            "game_id": game_id,
            "current_fen": fen,
            "bot_level": bot_level,
            "time_limit_ms": time_limit_ms
        }
        return await self.publish_game_update(game_id, message)

    async def publish_bot_move(self, game_id: int, move: str, confidence: float = 1.0) -> bool:
        """
        Publish a bot's calculated move.

        Args:
            game_id: Game ID
            move: Move in UCI format
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            True if published successfully
        """
        message = {
            "type": "bot_move",
            "game_id": game_id,
            "move": move,
            "confidence": confidence
        }
        return await self.publish_game_update(game_id, message)

    async def publish_game_state(self, game_id: int, game_data: Dict[str, Any]) -> bool:
        """
        Publish complete game state update.

        Args:
            game_id: Game ID
            game_data: Complete game state data

        Returns:
            True if published successfully
        """
        message = {
            "type": "game_state",
            "game_id": game_id,
            **game_data
        }
        return await self.publish_game_update(game_id, message)


# Global Redis client instance
redis_client = RedisClient()