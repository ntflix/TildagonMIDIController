from .ESPNOWMessageType import ESPNOWMessageTypes
from .Room import Room
from .Comms import Comms
from .MIDIEvent import MIDIEvent


class ESPNOWMIDIComms:
    """
    ESP-NOW communication layer for MIDI events.

    Implements the Peer (ESP-NOW Sender) side of the ESPNOWMIDIBridge protocol.
    Sends MIDI event frames via ESP-NOW to the bridge host.
    """

    def __init__(self):
        """Initialize communications."""
        self.comms = Comms()
        self.local_mac = self.get_local_mac()
        self.bridge_mac = None
        self.connected = False

    def get_local_mac(self) -> bytes:
        """Get the local ESP32's MAC address."""
        return self.comms.mac

    def set_bridge_mac(self, mac: bytes) -> None:
        """Set the bridge MAC address and add it as a peer."""
        if len(mac) != 6:
            raise ValueError("MAC address must be 6 bytes")
        self.bridge_mac = mac
        self.connected = True

    async def join_a_room(self) -> Room:
        room = await self.comms.join_a_room()
        self.set_bridge_mac(room.host_mac)
        return room

    async def send_midi_event(self, midi_event: MIDIEvent) -> bool:
        """
        Send a MIDI event to the bridge via ESP-NOW.

        The Raw MIDI Frame contains:
        [SOURCE_MAC (6)] [CHANNEL (1)] [EVENT_TYPE (1)] [DATA1 (1)] [DATA2 (1)]
        [SYSEX_LEN (1)] [SYSEX_DATA (0-246)]

        Args:
            midi_event: MIDIEvent instance

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.bridge_mac:
            print("ERROR: Bridge MAC not set")
            return False

        try:
            # Serialize the MIDI event to raw frame (11 + sysex_len bytes)
            raw_frame = midi_event.serialize()
            print(f"Sending MIDI event {raw_frame} to {self.bridge_mac.hex()}")
            await self.comms.send_async(
                self.bridge_mac, ESPNOWMessageTypes.DATA, raw_frame
            )
            return True

        except Exception as e:
            print(f"ERROR sending MIDI event: {e}")
            return False

    def reset(self) -> None:
        """Reset communications."""
        self.comms.reset()
        self.local_mac = self.get_local_mac()
        self.bridge_mac = None
        self.connected = False
