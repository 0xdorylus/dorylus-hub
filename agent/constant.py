from enum import Enum

class UserLevel(Enum):
    GUEST:int= 0
    NORMAL:int= 1
    VIP :int= 2

class UserType(Enum):
    Sign:int= 1
    Device:int= 3
    Email :int= 2

class AssistantNumLimit(Enum):
    NORMAL_NUM = 3
    VIP_NUM = 10
    ADMIN_NUM = 30