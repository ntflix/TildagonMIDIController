from .MACAddress import MACAddress


class Room:
    id: int
    host_mac: MACAddress

    def __str__(self) -> str:
        return f"Room(id={self.id}, host_mac={self.host_mac.hex()})"

    def __init__(self, id: int, host_mac: MACAddress):
        self.id = id
        self.host_mac = host_mac
