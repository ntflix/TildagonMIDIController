# TildagonMIDI

Sends encoded MIDI messages over ESP-NOW. This is the client side, which runs on the MIDI controller device. It encodes MIDI messages and sends them to the ESPNOWMIDIBridge server (which runs on another ESP32 device which talks to a host computer running ALSAMIDISource over COBS-framed UART messages) using ESP-NOW.
