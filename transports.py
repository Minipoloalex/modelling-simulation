from enum import Enum

class TransportType(Enum):
    WALK = 0
    BIKE = 1
    ELECTRIC_SCOOTER = 2
    CAR = 3

TRANSPORTS = [TransportType.WALK, TransportType.BIKE, TransportType.ELECTRIC_SCOOTER, TransportType.CAR]
