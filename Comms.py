from typing import Callable
from .Magic import MAGIC
import aioespnow
import asyncio
from .ESPNOWMessageType import ESPNOWMessageTypes
from .Room import Room
from .MACAddress import MACAddress
from .WiFiReset import wifi_reset


class Comms:
    broadcast_setup: bool = False

    def __init__(self):
        # A WLAN interface must be active to send()/recv()
        self.sta = wifi_reset()  # Reset wifi to AP off, STA on and disconnected

        self.e = aioespnow.AIOESPNow()
        self.e.config(timeout_ms=5000)
        print("ESP32 STA channel:", self.sta.config("channel"))
        self.e.active(True)

    def reset(self) -> None:
        self.__init__()

    def get_size_of_message(self, message: bytes | str) -> int:
        """Get the size of the message in bytes."""
        if isinstance(message, str):
            message = message.encode()
        return len(message)

    async def send_async(
        self,
        addr: bytes,
        message_type: int,
        message: bytes = b"",
    ) -> None:
        """Send a message to a peer asynchronously."""
        message = MAGIC + bytes([message_type]) + message

        print(f"Sending message {message} to {addr.hex()} async")
        if self.get_size_of_message(message) > 250:
            raise ValueError(
                f"Oops! Message size {self.get_size_of_message(message)} exceeds maximum allowed size of 250 bytes."
            )
        await self.e.asend(addr, message)

    def send_sync(
        self,
        addr: bytes,
        message_type: int,
        message: bytes = b"",
    ) -> None:
        """Send a message to a peer synchronously."""
        message = MAGIC + bytes([message_type]) + message

        print(f"Sending message {message} to {addr.hex()} sync")
        if self.get_size_of_message(message) > 250:
            raise ValueError(
                f"Oops! Message size {self.get_size_of_message(message)} exceeds maximum allowed size of 250 bytes."
            )
        self.e.send(addr, message)

    async def receive(self, recv_async: bool = True) -> tuple[bytes, bytes] | None:
        """Receive a message from a peer.
        Returns:
            tuple[bytes, bytes] | None: A tuple containing the host's MAC address and the message bytes,
            or None if no message was received within the timeout.
        """
        host: bytes
        msg: bytes | None = None

        if recv_async:
            host, msg = await self.e.arecv()
        else:
            host, msg = self.e.recv()

        if msg:
            print(f"`comms.py`: Received message from {host}: `{msg}`")
            return host, msg
        else:
            print("Timeout")
            return None

    async def __wait_until_receive(self) -> tuple[bytes, bytes]:
        """Wait until a message is received from a peer.
        Returns:
            tuple[bytes, bytes]: A tuple containing the host's MAC address and the message bytes.
        """
        while True:
            result = await self.receive(recv_async=True)
            if result:
                return result

    async def wait_for_room(self) -> Room:
        """Discover available rooms by listening for broadcast JOIN requests.
        Returns:
            Room: The discovered Room instance.
        """

        while True:
            message = await self.__wait_until_receive()
            if message:
                host, msg = message
                room = self.parse_message(host, msg)
                if room:
                    print(f"Discovered room: {room}")
                    return room

    async def join_a_room(self) -> Room:
        """
        Join a room by waiting for wait_for_room() to discover it, then sending a JOIN message to the host.
        Returns:
            Room: The Room instance that was joined.
        """
        room = await self.wait_for_room()
        print(f"Joining room: {room}")

        self.e.add_peer(room.host_mac)
        await asyncio.sleep_ms(250)
        # Send a JOIN message to the host
        await self.send_async(room.host_mac, ESPNOWMessageTypes.JOIN, bytes([room.id]))
        print(f"Sent JOIN message to {room.host_mac.hex()}")

        room_ack = await self.__wait_until_receive()
        print(f"Received room ack: {room_ack}")

        return room

    def parse_message(self, host: bytes, msg: bytes) -> Room | None:
        """Parse a message according to the protocol.
        Args:
            host (bytes): The MAC address of the host sending the message.
            msg (bytes): The raw message bytes received from the host.
        """
        print(f"Parsing message from {host.hex()}: {msg}")

        # Check for the MAGIC bytes, the message type, and then extract the room ID and capabilities
        if not msg.startswith(MAGIC):
            raise ValueError("Invalid message: missing MAGIC bytes")
        if len(msg) < 5:
            raise ValueError(
                "Invalid message: too short to contain MAGIC and message type"
            )
        magic = msg[:4]
        message_type = msg[4]
        if message_type == ESPNOWMessageTypes.JOIN:
            pass  # We are not hosting a room
        elif message_type == ESPNOWMessageTypes.LEAVE:
            pass  # We are not hosting a room
        elif message_type == ESPNOWMessageTypes.DATA:
            pass  # This is application-specific data, we will handle it in the client app
        elif message_type == ESPNOWMessageTypes.ADVERTISEMENT:
            room_id = msg[5]
            capabilities = msg[6:]
            print(
                f"Received room advertisement: room_id={room_id}, capabilities={capabilities}"
            )
            return Room(id=room_id, host_mac=host)
        else:
            print("msg:", msg)
            print("magic: ", magic)
            print(message_type)
            raise ValueError(f"Unknown message type: {message_type}")

    @property
    def mac(self) -> bytes:
        """Local MAC address"""
        return self.sta.config("mac")
