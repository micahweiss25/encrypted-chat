from typing import Tuple
import asyncio

class Client():
    """Store incoming messages."""
    def __init__(self, pub_key, host, port):
        self.pub_key = pub_key
        self.host: str = host
        self.listener_port = port
        self.messages: list[str] = []

    async def get_messages(self):
        """Retrieve and clear the client's messages."""
        msgs = self.messages[:]
        self.messages.clear()
        return msgs

    async def reader_loop(self):
        """Continuously read messages from the client."""
        while True:
            await asyncio.sleep(1)
            for message in await self.get_messages():
                print(f"{self.host} - {message}")