# ESPNOWMIDIClientUI.py


import time

from app_components import clear_background
from events.input import BUTTON_TYPES, ButtonDownEvent, ButtonUpEvent

from .Drawing import Drawing
from .Focusable import Focusable
from .ESPNOWMIDIComms import ESPNOWMIDIComms
from .MIDIEvent import MIDIEvent


class ESPNOWMIDIClientUI(Focusable):
    NOTE_OFFSETS = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "A": -3,
        "B": -1,
    }

    BUTTON_NOTE_NAMES = {
        "UP": "A",
        "RIGHT": "B",
        "CONFIRM": "C",
        "DOWN": "D",
        "LEFT": "E",
        "CANCEL": "F",
    }

    def __init__(self, midi_comms: ESPNOWMIDIComms, octave: int = 4):
        self.midi_comms = midi_comms
        self.drawing = Drawing()
        self.current_octave = octave
        self.current_velocity = 100
        self.current_channel = 0
        self.last_sent_event = None
        self.last_sent_time = 0
        self.held_buttons = set()

    def _base_note_for_octave(self, octave: int) -> int:
        return 12 * (octave + 1)

    def _midi_note_for_button(self, button_name: str):
        note_name = self.BUTTON_NOTE_NAMES.get(button_name)
        if note_name is None:
            return None
        note = (
            self._base_note_for_octave(self.current_octave)
            + self.NOTE_OFFSETS[note_name]
        )
        return max(0, min(127, note))

    def _note_label_for_button(self, button_name: str):
        note_name = self.BUTTON_NOTE_NAMES.get(button_name)
        if note_name is None:
            return None
        return f"{note_name}{self.current_octave}"

    def _button_name(self, button) -> str | None:
        current = button
        while current is not None:
            for name, button_type in BUTTON_TYPES.items():
                if current == button_type:
                    return name
            current = getattr(current, "parent", None)
        return None

    def handle_button_down(self, event):
        print(f"Button down event: {event}")
        button_name = self._button_name(event.button)
        print("Resolved button down:", button_name)
        if button_name not in self.BUTTON_NOTE_NAMES:
            return None
        if button_name in self.held_buttons:
            return None

        self.held_buttons.add(button_name)
        return self._build_midi_event(button_name, note_on=True)

    def handle_button_up(self, event):
        print(f"Button up event: {event}")
        button_name = self._button_name(event.button)
        print("Resolved button up:", button_name)
        if button_name not in self.BUTTON_NOTE_NAMES:
            return None

        if button_name in self.held_buttons:
            self.held_buttons.remove(button_name)

        return self._build_midi_event(button_name, note_on=False)

    def _build_midi_event(self, button_name: str, note_on: bool) -> MIDIEvent | None:
        midi_note = self._midi_note_for_button(button_name)
        note_label = self._note_label_for_button(button_name)
        if midi_note is None or note_label is None:
            return None

        event_type = MIDIEvent.NOTE_ON if note_on else MIDIEvent.NOTE_OFF

        midi_event = MIDIEvent(
            source_mac=self.midi_comms.local_mac,
            midi_channel=self.current_channel,
            event_type=event_type,
            data_byte_1=midi_note,
            data_byte_2=self.current_velocity if note_on else 0,
        )

        direction = "↓" if note_on else "↑"
        verb = "ON" if note_on else "OFF"
        self.last_sent_event = (
            f"{direction} {button_name} {note_label} {verb} ({midi_note})"
        )
        self.last_sent_time = time.ticks_ms()

        print(
            f"Built MIDI event for {button_name}: "
            f"{'NOTE ON' if note_on else 'NOTE OFF'} {midi_note}"
        )
        return midi_event

    def draw(self, ctx) -> None:
        clear_background(ctx)
        ctx.font = "sans-serif"
        ctx.font_size = 20
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        self._draw_main(ctx)

    def _draw_main(self, ctx) -> None:
        ctx.font_size = 14
        ctx.rgb(1, 1, 1).move_to(0, -96).text("MIDI Client")

        bridge_mac = self.midi_comms.bridge_mac
        bridge_connected = bridge_mac is not None
        ctx.font_size = 10
        ctx.rgb(0, 0.8, 0).move_to(0, -78).text(
            f"Bridge: {bridge_mac.hex()}" if bridge_connected else "Bridge: not set"
        )

        ctx.font_size = 12
        ctx.rgb(1, 1, 1).move_to(0, -52).text(f"Octave: {self.current_octave}")
        ctx.rgb(1, 1, 1).move_to(0, -34).text(f"Channel: {self.current_channel}")
        ctx.rgb(1, 1, 1).move_to(0, -16).text(f"Velocity: {self.current_velocity}")

        ctx.font_size = 10
        ctx.rgb(0.9, 0.9, 0.9).move_to(0, 10).text("UP=A  RIGHT=B  CONFIRM=C")
        ctx.rgb(0.9, 0.9, 0.9).move_to(0, 24).text("DOWN=D  LEFT=E  CANCEL=F")
        ctx.rgb(0.8, 0.8, 0.8).move_to(0, 42).text(
            "Press = NOTE ON, release = NOTE OFF"
        )

        held = " ".join(sorted(self.held_buttons)) if self.held_buttons else "none"
        ctx.font_size = 9
        ctx.rgb(0.8, 0.8, 0.8).move_to(0, 62).text(f"Held: {held}")

        if self.last_sent_event:
            elapsed = time.ticks_ms() - self.last_sent_time
            if elapsed < 1500:
                ctx.font_size = 11
                ctx.rgb(0, 0.9, 0).move_to(0, 84).text(self.last_sent_event)
