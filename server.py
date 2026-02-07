from Crypto.PublicKey import RSA
from typing import Tuple
import logging
import Crypto.Cipher.AES as AES
import Crypto.Random as Random
import datetime
import asyncio
import config


class Server():
    """Store the server's information and any registered clients."""
    def __init__(self):
        self.priv_key, self.pub_key = self.generate_key()
        self.clients = {}
        self.host = config.get_settings().HOST
        self.port = config.get_settings().PORT
        self.key_lenght = config.get_settings().KEY_LENGTH
        self.max_message_size = config.get_settings().MAX_MESSAGE_SIZE

    async def register_peer(self, client_address: Tuple[str, int]) -> bool:
        """Register a new client with their public key."""
        client_host, client_port = client_address

        if client_host not in self.clients:
            reader, writer = None, None
            try:
                reader, writer = await asyncio.open_connection(
                                                        client_host,
                                                        client_port
                                                    )
            except ConnectionRefusedError as e:
                logging.error(f"Failed to connect to peer {client_host}:{client_port} - {e}")
                return False

            writer.write(self.pub_key)
            pub_key = await reader.read(self.key_lenght)
            client = Client(pub_key, client_host, client_port)
            self.clients[client_host] = client
            logging.info("Registered new peer: %(client_host)%")
            return True
        else:
            logging.info("Peer already registered: %(client_host)%")
            return False
    
    @classmethod
    async def handle_connection(cls, self, reader, writer):
        """Handle an incoming client connection."""
        client_address: Tuple[str, int] = writer.get_extra_info('peername')
        client_host, client_port = client_address

        # Accept incoming registration request
        if client_host not in self.clients:
            self.register_peer(client_address)
        else:
            client: Client = self.clients[client_host]
            encyrpted_message = await reader.read(self.max_message_size)
            priv_key = RSA.import_key(self.priv_key)
            decrypted_message = priv_key.decrypt(encyrpted_message)
            client.messages.append(f"{datetime.datetime.now()} - "
                                    f"{decrypted_message}")
            logging.info("Message from: %(client_host)%")

    async def start(self):
        """Start the server to listen for incoming connections."""
        self.listener = await asyncio.start_server(
                        self.handle_connection,
                        self.host,
                        self.port
                    )

        logging.debug("Server started, waiting for connections...")

    def end(self):
        """Shut down the server and close all client connections."""
        self.listener.close()
        logging.debug("Server shut down.")

    @classmethod
    def generate_key(cls):
        """Generate a new encryption key."""
        random = Random.new().read
        rsa_key = RSA.generate(2048, random)
        private_key = rsa_key.exportKey()
        public_key = rsa_key.publickey().exportKey()
        return private_key, public_key
