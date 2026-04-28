import asyncio

from app import App
from app_components import clear_background
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent
from events.input import Buttons, ButtonDownEvent, ButtonUpEvent

from .ESPNOWMIDIComms import ESPNOWMIDIComms
from .ESPNOWMIDIClientUI import ESPNOWMIDIClientUI


class ESPNOWMIDIClient(App):
    request_fast_updates = False

    def __init__(self):
        self.overlays = []
        self.cleared = False
        self.button_states = Buttons(self)
        self.midi_comms = ESPNOWMIDIComms()
        self.ui = ESPNOWMIDIClientUI(self.midi_comms)
        self.pending_midi = []

        eventbus.on(ButtonDownEvent, self.handle_button_down, self)
        eventbus.on(ButtonUpEvent, self.handle_button_up, self)

    async def run(self, render_update):
        await render_update()
        await self.midi_comms.join_a_room()

        print("App comms object:", self.midi_comms)
        print("App comms bridge_mac:", self.midi_comms.bridge_mac)

        await render_update()

        while True:
            while self.pending_midi:
                midi_event = self.pending_midi.pop(0)
                print("Sending queued MIDI event:", midi_event)
                try:
                    success = await self.midi_comms.send_midi_event(midi_event)
                    print("send_midi_event result:", success)
                except Exception as e:
                    print("send_midi_event exception:", e)

            await render_update()
            await asyncio.sleep_ms(20)

    def draw(self, ctx):
        if not self.cleared:
            clear_background(ctx)
            self.cleared = True
        ctx.save()
        self.ui.draw(ctx)
        ctx.restore()

    def update(self, delta: int):
        return False

    def handle_button_down(self, event: ButtonDownEvent):
        print(f"APP button down: {event}")
        midi_event = self.ui.handle_button_down(event)
        print("APP midi_event from down:", midi_event)
        if midi_event is not None:
            self.pending_midi.append(midi_event)

    def handle_button_up(self, event: ButtonUpEvent):
        print(f"APP button up: {event}")
        midi_event = self.ui.handle_button_up(event)
        print("APP midi_event from up:", midi_event)
        if midi_event is not None:
            self.pending_midi.append(midi_event)

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = ESPNOWMIDIClient
