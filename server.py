from Crypto.PublicKey import RSA
from typing import Tuple
import logging
import Crypto.Cipher.AES as AES
import Crypto.Random as Random
import datetime
import asyncio
import config
from client import Client
from message import Message


class Server():
    """Store the server's information and any registered clients."""
    def __init__(self):
        self.priv_key, self.pub_key = self.generate_key()
        self.clients = {}
        self.host = config.get_settings().HOST
        self.port = config.get_settings().PORT
        self.key_lenght = config.get_settings().KEY_LENGTH
        self.max_message_size = config.get_settings().MAX_MESSAGE_SIZE
        self.registration_msg = Message().write_msg(
            "REGISTER",
            self.pub_key.decode(),
            self.port
        )

    async def register_peer(self, pub_key: str, host: str, port: int) -> None:
        """Register a new client with their public key."""
        if host in self.clients:
            logging.debug("Peer %s:%s is already registered.", host, port)

        self.clients[host] = Client(pub_key, host, port)
        logging.debug("Registered peer %s:%s with public key %s", host, port, pub_key)

    async def send_message(self, host: str, listener_port: int, message_id: int, *args) -> None:
        """Send a message to a registered client."""
        reader, writer = await asyncio.open_connection(host, listener_port)

        if message_id == Message.MsgID.TEXT.value:
            if len(args) != 1:
                logging.debug("Invalid arguments for text message. Expected (message).")
            else:
                message = args[0]
                writer.write(Message().write_msg(Message.MsgID.TEXT.name, message))
                response_message = await reader.read(self.max_message_size)
                try:
                    # Expect an ack of received, invalid, or unregistered message in response
                    msg_name, ack_name = Message().read_msg(response_message)
                    if ack_name == Message.AckID.UNREGISTERED.name:
                        await self.half_registration_resp(reader, writer)
                    elif ack_name == Message.AckID.INVALID.name:
                        logging.debug("Peer %s:%s received an invalid message. Message was not delivered.",
                            host, listener_port)
                    elif ack_name == Message.AckID.RECEIVED.name:
                        logging.debug("Peer %s:%s successfully received message.",
                            host, listener_port)
                    else:
                        logging.debug("Unhandled ack name from %s:%s: %s",
                            host, listener_port, ack_name)
                except ValueError as e:
                    logging.debug("Received invalid ack message from %s:%s: %s",
                        host, listener_port, e)
        # Initiate Full Registration
        elif message_id == Message.MsgID.REGISTER.value:
            if len(args) != 0:
                logging.debug("Invalid arguments for register message. Expected (pub_key, port).")
            else:
                await self.full_registration_init(reader, writer)
        else:
            logging.debug("Unhandled message id: %s", message_id)

        writer.close()

    async def half_registration_init(self, reader, writer):
        """
        Initiate half registration by sending an ACK_UNREGISTERED message to the peer and waiting their registration message back.
        Finally, send an ack back to the peer to confirm whether registration was successful or not.

        In this scenario, the peer attempted to send you a message without registering first, implying you are already registered by them.

        ARGS:
            reader: The reader to read the response from the peer.
            writer: The writer to send the registration message to the peer.

        RAISES:
            ValueError: If the response message is invalid or if the ack message is invalid.
        
        RETURN: None
        """
        writer.write(
            Message().write_msg(
                Message.MsgID.ACK.name,
                Message.AckID.UNREGISTERED.value
            )
        )
        # wait for registration message back from peer
        response = await reader.read(self.max_message_size)
        try:
            msg_name, pub_key, listener_port = Message().read_msg(response)
            if msg_name != Message.MsgID.REGISTER.name:
                logging.debug("Expected registration message from %s:%s: %s", host, sender_port, msg_name)
            else:
                self.register_peer(pub_key=pub_key, host=host, port=listener_port)
                writer.write(Message().write_msg(Message.MsgID.ACK.name, Message.AckID.RECEIVED.value))
        except ValueError as e:
            logging.debug("Received invalid registration message from %s:%s: %s", host, sender_port, e)
            writer.write(Message().write_msg(Message.MsgID.ACK.name, Message.AckID.INVALID.value))
            return

    async def half_registration_resp(self, reader, writer):
        """
        Respond to a half registration request (ACK_UNREGISTERED) by sending a registration message to
        the peer and waiting for an ack back to confirm whether registration was successful or not.

        ARGS:
            reader: The reader to read the response from the peer.
            writer: The writer to send the registration message to the peer.
        RAISES:
            ValueError: If the response message is invalid or if the ack message is invalid.
        RETURN: None
        """
        host, sender_port = writer.get_extra_info('peername')
        logging.debug("Peer %s:%s requested registration", host, sender_port)
        writer.write(self.registration_msg)
        # Excpect an ack back
        registration_response = await reader.read(self.max_message_size)
        try:
            msg_name, ack_name = Message().read_msg(registration_response)
            if ack_name == Message.AckID.RECEIVED.name:
                logging.debug("Successfully registered peer %s:%s",
                    client.host, client.listener_port)
            else:
                logging.debug("Expected ack of RECEIVED for registration message from %s:%s, but got: %s",
                    client.host, client.listener_port, ack_name)
        except ValueError as e:
            logging.debug("Received invalid ack message from %s:%s: %s",
                client.host, client.listener_port, e)

    async def full_registration_init(self, reader, writer):
        """
        Initiate full registration by sending a registration message to the peer and waiting for a
        registration message back from the peer. Finally, send an ack back to the peer to confirm whether
        registration was successful or not.

        ARGS:
            reader: The reader to read the response from the peer.
            writer: The writer to send the registration message to the peer.
        RAISES:
            ValueError: If the response message is invalid or if the ack message is invalid.
        RETURN: None
        """
        writer.write(self.registration_msg)
        response = await reader.read(self.max_message_size)
        try:
            msg_name, pub_key, listener_port = Message().read_msg(response)
            if msg_name != Message.MsgID.REGISTER.name:
                logging.debug("Expected registration message from %s:%s: %s", host, sender_port, msg_name)
            else:
                await self.register_peer(pub_key=self.pub_key, host=self.host, port=self.port)
                writer.write(Message().write_msg(Message.MsgID.ACK.name, Message.AckID.RECEIVED.value))
        except ValueError as e:
            logging.debug("Received invalid registration message from %s:%s: %s", host, sender_port, e)
            writer.write(Message().write_msg(Message.MsgID.ACK.name, Message.AckID.INVALID.value))
            return

    async def full_registration_resp(self, reader, writer, message):
        host, sender_port = writer.get_extra_info('peername')
        pub_key, listener_port = message[1], message[2]
        # Attempt to register peer
        await self.register_peer(pub_key=pub_key, host=host, port=listener_port)
        # Respond with your own registration message. Use the port they connected with to avoid registration loop
        writer.write(self.registration_msg)
        # Check if registration is successful
        response_msg = await reader.read(self.max_message_size)
        try:
            msg_name, ack_name = Message().read_msg(response_msg)
            if ack_name != Message().AckID.RECEIVED.name:
                logging.debug("Registration of peer %s:%s was not successful: %s", host, sender_port, ack_name)
            elif ack_name == Message().AckID.RECEIVED.name:
                logging.debug("Registration of peer %s:%s successful: %s", host, sender_port, ack_name)
            else:
                logging.debug("Unhandled case")
        except ValueError as e:
            logging.debug("Received invalid ack message from %s:%s: %s", host, sender_port, e)

        writer.close()

    async def do_text_message(self, reader, writer, message):
        # Check if the sender is registered so we know where to file the message
        host, sender_port = writer.get_extra_info('peername')
        client = self.clients.get(host)
        # Peer is unregistered
        # Initiate Half Registration
        if not client:
            logging.debug("Received message from unregistered sender %s:%s", host, sender_port)
            await self.half_registration_init(reader, writer)

            client = self.clients.get(host)

        # Peer is registered. Store the message and send an ack
        client.messages.append(message[1])
        writer.write(
            Message().write_msg(
                Message.MsgID.ACK.name,
                Message.AckID.RECEIVED.value
            )
        )

    async def handle_connection(self, reader, writer):
        """Handle an incoming client connection."""
        host, sender_port = writer.get_extra_info('peername')
        data = await reader.read(self.max_message_size)
        message = None
        try:
            message = Message().read_msg(data)
        except ValueError as e:
            logging.debug("Received invalid message from %s:%s: %s", writer.get_extra_info('peername'), e)
            writer.close()
            return

        msg_name = message[0]

        # Sender initiates registration by sending a register message
        if msg_name == Message.MsgID.REGISTER.name:
            try:
                await self.full_registration_resp(reader, writer, message)
            except Exception as e:
                logging.debug("Error handling registration message from %s:%s: %s", host, sender_port, e)
        # Sender sends a text message
        elif msg_name == Message.MsgID.TEXT.name:
            try:
                await self.do_text_message(reader, writer, message)
            except Exception as e:
                logging.debug("Error handling text message from %s:%s: %s", host, sender_port, e)
        else:
            logging.debug("Received invalid message name from %s:%s: %s", host, sender_port, msg_name)

        writer.close()


    async def start(self):
        """Start the server to listen for incoming connections."""
        self.listener = await asyncio.start_server(
                        self.handle_connection,
                        self.host,
                        self.port
                    )

        logging.debug("Server started, on %s:%s...", self.host, self.port)

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
