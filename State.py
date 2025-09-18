from enum import Enum

class State(Enum):
    NULL = "null"
    REQUEST = "request"
    SC = "sc"
    RELEASE = "release"