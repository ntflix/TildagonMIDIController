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

        eventbus.on(ButtonDownEvent, self.handle_button_down, self)
        eventbus.on(ButtonUpEvent, self.handle_button_up, self)

    async def run(self, render_update):
        # One render before join (optional)
        await render_update()

        # Join room (blocking until connected)
        await self.midi_comms.join_a_room()

        # One render after join to show "connected to {mac}"
        await render_update()

        # Main loop: no UI update, no timer
        while True:
            await asyncio.sleep_ms(0)

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
        midi_event = self.ui.handle_button_down(event)
        if midi_event is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.midi_comms.send_midi_event(midi_event))

    def handle_button_up(self, event: ButtonUpEvent):
        midi_event = self.ui.handle_button_up(event)
        if midi_event is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.midi_comms.send_midi_event(midi_event))

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))


__app_export__ = ESPNOWMIDIClient
