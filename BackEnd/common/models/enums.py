from enum import Enum

class Gender(Enum):
    male = "male"
    female = "female"

class Speaker(Enum):
    PARENT = "parent"
    CHILD = "child"
    ROBOT = "robot"