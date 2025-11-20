from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"

class Speaker(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    ROBOT = "robot"