from Crypto.PublicKey import RSA
import argparse
import shlex
import Crypto.Cipher.AES as AES
import Crypto.Random as Random
import datetime
import asyncio
import logging
import threading
from typing import Tuple
import cmd

KEY_LENGTH = 2048
MAX_MESSAGE_SIZE = 1024

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)


class Client():
    """Store incoming messages."""
    def __init__(self, pub_key, address, reader, writer):
        self.pub_key = pub_key
        self.address: Tuple[str, int] = address
        self.host: str = address[0]
        self.port: int = address[1]
        self.messages: list[str] = []

    async def get_messages(self):
        """Retrieve and clear the client's messages."""
        msgs = self.messages[:]
        self.messages.clear()
        return msgs


class Server():
    """Store the server's information and any registered clients."""
    def __init__(self):
        self.priv_key, self.pub_key = self.generate_key()
        self.clients = {}

    async def register_peer(self, address: Tuple[str, int]):
        """Register a new client with their public key."""
        if address[0] not in self.clients:
            reader, writer = await asyncio.open_connection(
                                                    address[0],
                                                    address[1]
                                                )
            writer.write(self.pub_key)
            pub_key = await reader.read(KEY_LENGTH)
            client = Client(pub_key, address, reader, writer)
            self.clients[address] = client
            logging.info("Registered new peer: %(address)%")
        else:
            logging.info("Peer already registered: %(address)%")

    async def open_chat(self, address):
        """Open a chat with 'address'."""
        pass

    @classmethod
    async def handle_connection(cls, self, reader, writer):
        """Handle an incoming client connection."""
        address: Tuple[str, int] = writer.get_extra_info('peername')
        host: str = address[0]

        # Accept incoming registration request
        if address[0] not in self.clients:
            self.register_peer(address)
        else:
            client: Client = self.clients[host]
            encyrpted_message = await reader.read(MAX_MESSAGE_SIZE)
            priv_key = RSA.import_key(self.priv_key)
            decrypted_message = priv_key.decrypt(encyrpted_message)
            client.messages.append(f"{datetime.datetime.now()} - "
                                    f"{decrypted_message}")
            logging.info("Message from: %(address)%")

    async def start(self):
        """Start the server to listen for incoming connections."""
        server = await asyncio.start_server(
                        self.handle_connection,
                        '0.0.0.0',
                        8888
                    )

        logging.debug("Server started, waiting for connections...")
        async with server:
            await server.serve_forever()

    @classmethod
    def generate_key(cls):
        """Generate a new encryption key."""
        random = Random.new().read
        rsa_key = RSA.generate(2048, random)
        private_key = rsa_key.exportKey()
        public_key = rsa_key.publickey().exportKey()
        return private_key, public_key


class Chat():
    """Base class for chat functionality."""
    def __init__(self, server: Server, client: Client):
        self.server = server
        self.client = client

    async def start(self):
        """Start the chat session."""

        # await asyncio.gather(
        #     self.send_message_loop(),
        #     self.read_messages()
        # )

    async def send_message(self, message: str):
        """Send a message to the client."""
        _, writer = await asyncio.open_connection(
                                                    self.client.host,
                                                    self.client.port
                                                )
        pub_key = RSA.import_key(self.client.pub_key)
        encrypted_message = pub_key.encrypt(message.encode(), 32)[0]
        writer.write(encrypted_message)

    async def read_messages(self):
        """Read messages as they arrive."""
        while True:
            if self.client.messages:
                print(self.client.messages.pop(0))


class ChatMenu(cmd.Cmd):
    """Command line interface for a chat session."""
    intro = "Starting chat session. Type help or ? to list commands.\n"
    prompt = "(chat) "

    def __init__(self, chat: Chat):
        super().__init__()
        self.chat = chat
        self.read_message_loop = asyncio.create_task(self.chat.read_messages())

    def do_send(self, arg):
        """Send a message: send <message>"""
        message = arg.strip()
        if not message:
            print("Usage: send <message>")
            return
        asyncio.create_task(self.chat.send_message(message))

    def do_exit(self, _):
        """Exit the chat session."""
        print("Exiting chat session...")
        self.read_message_loop.cancel()
        return True


class MainMenu(cmd.Cmd):
    """Command line interface for the chat application."""
    intro = "Welcome to the Encrypted Chat. Type help or ? to list commands.\n"
    prompt = "(encrypted-chat) "

    def __init__(self, server: Server):
        super().__init__()
        self.server = server

    def do_register(self, arg):
        """Register a new peer: register <host> <port>"""
        args = shlex.split(arg)
        if len(args) != 2:
            print("Usage: register <host> <port>")
            return
        host, port = args[0], int(args[1])
        asyncio.create_task(self.server.register_peer((host, port)))

    def do_list_peers(self, _):
        """List all registered peers."""
        if not self.server.clients:
            print("No registered peers.")
            return
        for client in self.server.clients.values():
            print(f"Peer: {client.host}")

    def do_chat(self, arg):
        """Open a chat with a registered peer: chat <host>"""
        args = shlex.split(arg)
        if len(args) != 1:
            print("Usage: chat <host>")
            return
        host: str = args[0]
        client: Client = self.server.clients.get(host)
        chat = Chat(self.server, client)
        chat_menu = ChatMenu(chat)
        chat_menu.cmdloop()


    def complete_chat(self, text, _):
        """Autocomplete for chat command."""
        peers = [client.host for client in self.server.clients.values()]
        if not text:
            return peers
        else:
            return [peer for peer in peers if peer.startswith(text)]

    def do_exit(self, _):
        """Exit the chat application."""
        print("Exiting...")
        return True


async def main():
    """
    Main entry point for the chat application.
    """
    server: Server = Server()
    parser = argparse.ArgumentParser(description="Encrypted Chat Application")
    parser.add_argument('--host', '-H', type=str, default='0.0.0.0',
                        help='Address to listen on (default: 0.0.0.0)')
    server_connection = await asyncio.start_server(
                    server.handle_connection,
                    parser.parse_args().host,
                    8888
                )

    logging.debug("Server started, waiting for connections...")
    menu = MainMenu(server)
    thread = threading.Thread(target=menu.cmdloop(), daemon=True)
    thread.start()
    server_connection.close()

if __name__ == "__main__":
    asyncio.run(main())
