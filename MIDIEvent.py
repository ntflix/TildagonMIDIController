class MIDIEvent:
    """Helper class to build and serialize MIDI events."""

    # MIDI Event Type Constants
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLY_AFTERTOUCH = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_AFTERTOUCH = 0xD0
    PITCH_BEND = 0xE0
    SYSEX = 0xF0

    def __init__(
        self,
        source_mac: bytes,
        midi_channel: int,
        event_type: int,
        data_byte_1: int = 0,
        data_byte_2: int = 0,
        sysex_data: bytes = b"",
    ):
        """
        Initialize a MIDI event.

        Args:
            source_mac: 6-byte MAC address (big-endian)
            midi_channel: MIDI channel (0-15)
            event_type: MIDI status byte (0x80-0xF0)
            data_byte_1: First data byte (0-127)
            data_byte_2: Second data byte (0-127)
            sysex_data: SysEx payload (0-246 bytes)
        """
        if len(source_mac) != 6:
            raise ValueError("MAC address must be 6 bytes")
        if not (0 <= midi_channel <= 15):
            raise ValueError("MIDI channel must be 0-15")
        if not (0 <= data_byte_1 <= 127):
            raise ValueError("Data byte 1 must be 0-127")
        if not (0 <= data_byte_2 <= 127):
            raise ValueError("Data byte 2 must be 0-127")
        if len(sysex_data) > 246:
            raise ValueError("SysEx data must be 0-246 bytes")

        self.source_mac = source_mac
        self.midi_channel = midi_channel & 0x0F
        self.event_type = event_type
        self.data_byte_1 = data_byte_1
        self.data_byte_2 = data_byte_2
        self.sysex_data = sysex_data

    def serialize(self) -> bytes:
        """Serialize the MIDI event to the wire format."""
        frame = bytearray()

        # SOURCE_MAC (6 bytes)
        frame.extend(self.source_mac)

        # MIDI_CHANNEL (1 byte)
        frame.append(self.midi_channel)

        # EVENT_TYPE (1 byte)
        frame.append(self.event_type)

        # DATA_BYTE_1 (1 byte)
        frame.append(self.data_byte_1)

        # DATA_BYTE_2 (1 byte)
        frame.append(self.data_byte_2)

        # SYSEX_LEN (1 byte)
        sysex_len = len(self.sysex_data)
        frame.append(sysex_len)

        # SYSEX_DATA (variable)
        frame.extend(self.sysex_data)

        return bytes(frame)
