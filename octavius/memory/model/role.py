from enum import Enum

class Role(str,Enum):
    user= "User"
    assistant= "Assistant"
    tool= "Tool"
