import asyncio
from typing import Dict, List

import redis.asyncio as aioredis
import json
from fastapi import WebSocket

import os

from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv("DB_NAME")
db_connection = os.getenv("DB_CONNECTION")
class ConnectionManager:
    def __init__(self):
        # 存放**的链接
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, uid: str, ws: WebSocket):
        # 链接
        print("ws0",ws)
        await ws.accept()
        self.active_connections[uid] = ws
        print("ws1",ws)

        print("connect ws:", uid)
        ws2 = self.active_connections.get(uid)
        print("connect:",ws2)
        print("ws2",ws)


    def disconnect(self, uid: str, ws: WebSocket):
        # 关闭时 移除ws对象
        print("del ws:",uid)
        if uid in self.active_connections:
            del self.active_connections[uid]

    async def batch_send(self, uids: List[str],message:str):
        for uid in uids:
            ws = self.active_connections.get(uid)
            if ws is not None:
                try:
                    await ws.send_text(message)
                    return True

                except RuntimeError as e:
                    return False
            else:
                return False
    async def send(self, uid: str,message:str):
        ws = self.active_connections.get(uid)
        if ws is not None:
            try:
                await ws.send_text(message)
                return True

            except RuntimeError as e:
                return False
        else:
            return False
            # print("no ws connection")
        # 关闭时 移除ws对象
manager = ConnectionManager()

class RedisPubSubManager:
    """
        Initializes the RedisPubSubManager.

    Args:
        host (str): Redis server host.
        port (int): Redis server port.
    """

    def __init__(self, host='localhost', port=6379):
        self.redis_host = host
        self.redis_port = port
        self.pubsub = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        """
        Establishes a connection to Redis.

        Returns:
            aioredis.Redis: Redis connection object.
        """
        return aioredis.Redis(host=self.redis_host,
                              port=self.redis_port,
                              auto_close_connection_pool=False)

    async def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        self.redis_connection = await self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def _publish(self, channel_id: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.

        Args:
            channel_id (str): Channel or room ID.
            message (str): Message to be published.
        """
        await self.redis_connection.publish(channel_id, message)

    async def subscribe(self, channel_id: str) -> aioredis.Redis:
        """
        Subscribes to a Redis channel.

        Args:
            channel_id (str): Channel or room ID to subscribe to.

        Returns:
            aioredis.ChannelSubscribe: PubSub object for the subscribed channel.
        """
        await self.pubsub.subscribe(channel_id)
        return self.pubsub

    async def unsubscribe(self, channel_id: str) -> None:
        """
        Unsubscribes from a Redis channel.

        Args:
            channel_id (str): Channel or room ID to unsubscribe from.
        """
        await self.pubsub.unsubscribe(channel_id)


class WebSocketManager:

    def __init__(self):
        """
        Initializes the WebSocketManager.

        Attributes:
            rooms (dict): A dictionary to store WebSocket connections in different rooms.
            pubsub_client (RedisPubSubManager): An instance of the RedisPubSubManager class for pub-sub functionality.
        """
        self.channels: dict = {}
        self.pubsub_client = RedisPubSubManager()

    async def add_user_to_room(self, channel_id: str, websocket: WebSocket) -> None:
        """
        Adds a user's WebSocket connection to a room.

        Args:
            channel_id (str): Room ID or channel name.
            websocket (WebSocket): WebSocket connection object.
        """
        await websocket.accept()

        if channel_id in self.channels:
            self.channels[channel_id].append(websocket)
        else:
            self.channels[channel_id] = [websocket]

            await self.pubsub_client.connect()
            pubsub_subscriber = await self.pubsub_client.subscribe(channel_id)
            asyncio.create_task(self._pubsub_data_reader(pubsub_subscriber))

    async def broadcast_to_room(self, channel_id: str, message: str) -> None:
        """
        Broadcasts a message to all connected WebSockets in a room.

        Args:
            channel_id (str): Room ID or channel name.
            message (str): Message to be broadcasted.
        """
        await self.pubsub_client._publish(channel_id, message)

    async def remove_user_from_room(self, channel_id: str, websocket: WebSocket) -> None:
        """
        Removes a user's WebSocket connection from a room.

        Args:
            channel_id (str): Room ID or channel name.
            websocket (WebSocket): WebSocket connection object.
        """
        self.channels[channel_id].remove(websocket)

        if len(self.channels[channel_id]) == 0:
            del self.channels[channel_id]
            await self.pubsub_client.unsubscribe(channel_id)

    async def _pubsub_data_reader(self, pubsub_subscriber):
        """
        Reads and broadcasts messages received from Redis PubSub.

        Args:
            pubsub_subscriber (aioredis.ChannelSubscribe): PubSub object for the subscribed channel.
        """
        while True:
            message = await pubsub_subscriber.get_message(ignore_subscribe_messages=True)
            if message is not None:
                channel_id = message['channel'].decode('utf-8')
                all_sockets = self.channels[channel_id]
                for socket in all_sockets:
                    data = message['data'].decode('utf-8')
                    await socket.send_text(data)