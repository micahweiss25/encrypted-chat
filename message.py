from enum import Enum
from typing import Tuple
import struct

class Message():
    """A message sent by a client to register with the server."""
    class MsgID(Enum):
        """Message to register with the server."""
        REGISTER = 1
        """Message to send a text message to a peer."""
        TEXT = 2
        """Message to acknowledge receipt of a message."""
        ACK = 3

    class AckID(Enum):
        """Message successfully received and processed."""
        RECEIVED = 1
        """Notify the sender that they are unregistered so they can send a registration message."""
        UNREGISTERED = 2
        """Notify the sender that the message was invalid and could not be processed."""
        INVALID = 3

    def write_msg(self, msg_name: str, *args) -> bytes:
        """Write a message to be sent to the server.
        
        Args:
            msg_name: The name of the message to write. Must be one of "register", "message", or "ack".
        Raises:
            ValueError: If the message name is invalid or if the arguments are invalid for the given message name.
        
        Returns:
            The bytes to be sent to the server.
        """
        # TODO: Get rid of plague of magic numbers here
        # Convert message id to message id name
        if msg_name == Message.MsgID.REGISTER.name:
            if len(args) != 2:
                raise ValueError("Invalid arguments for register message. Expected (pub_key, port).")
            else:
                pub_key, port = args[0], args[1]
                return struct.pack("!I", self.MsgID.REGISTER.value) + struct.pack("!I", len(pub_key)) + pub_key.encode() + struct.pack("!H", port)
        elif msg_name == Message.MsgID.TEXT.name:
            if len(args) != 1:
                raise ValueError("Invalid arguments for text message. Expected (message).")
            else:
                message = args[0]
                return struct.pack("!I", self.MsgID.TEXT.value) + struct.pack("!I", len(message)) + message.encode()
        elif msg_name == Message.MsgID.ACK.name:
            if len(args) != 1:
                raise ValueError("Invalid arguments for ack message. Expected (message_id).")
            else:
                ack_id = args[0]
                return struct.pack("!I", self.MsgID.ACK.value) + struct.pack("!I", ack_id)
        else:
            raise ValueError(f"Unhandled message name: {msg_name}")

    def read_msg(self, data) -> Tuple[str, str] or Tuple[str, str, int]:
        """Read a message received from the server.
        Args:
            data: The bytes received from the server.
        Raises:
            ValueError: If the message format is invalid or if the message type is invalid.
        Returns:
            A tuple containing the message type and the message data. The message type is one of "register" or "message". The message data is a string for "message" messages and a tuple of (pub_key, port) for "register" messages.
        """
        # TODO: Get rid of plague of magic numbers here
        id = struct.unpack("!I", data[:4])[0]
        # Convert message id to message  name
        msg_name = None
        try:
            msg_name = self.MsgID(id).name
        except ValueError:
            raise ValueError(f"Invalid message ID: {id}")

        if msg_name == Message.MsgID.TEXT.name:
            if len(data) < 8:
                raise ValueError("Invalid text message format. Expected at least 8 bytes for message ID and length.")
            else:
                length = struct.unpack("!I", data[4:8])[0]
                message = data[8:8+length].decode()
                return msg_name, message
        elif msg_name == Message.MsgID.REGISTER.name:
            if len(data) < 10:
                raise ValueError("Invalid register message format. Expected at least 10 bytes for message ID, key length, and port.")
            else:
                length = struct.unpack("!I", data[4:8])[0]
                pub_key = data[8:8+length].decode()
                port = struct.unpack("!H", data[8+length:10+length])[0]
                return msg_name, pub_key, port
        elif msg_name == Message.MsgID.ACK.name:
            if len(data) < 8:
                raise ValueError("Invalid ack message format. Expected at least 8 bytes for message ID and message ID.")
            else:
                ack_id = struct.unpack("!I", data[4:8])[0]
                ack_name = None
                try:
                    ack_name = self.AckID(ack_id).name
                except ValueError:
                    raise ValueError(f"Invalid ack ID: {ack_id}")

                return msg_name, ack_name

        else:
            raise ValueError(f"Unhandled message name: {msg_name}")