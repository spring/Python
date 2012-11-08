import re

### CATCH Functions
# Return Type, Function Name, Argumentlist 
CALLBACK_FUNCTIONS = re.compile("([_ ,a-zA-Z0-9\*]+)\(CALLING_CONV \*([a-zA-Z_0-9]+)\)\(([^\)]+)\);")

### CATCH Arguments
# done via str.split(",") no regex needed


### CATCH Enums
# enum name, enum values
ENUMS = re.compile("enum ([a-zA-Z]+) \{([a-zA-Z0-9=,\n\t _]+)\};")

### CATCH Enum values
# Name, Value
ENUM_VALUES = re.compile("([A-Z_]+)[ \t]+=[ \t]+([0-9]+),")

### CATCH Structs
STRUCTS = re.compile("struct [^ ]+ \{[^\}]+\}; //\$ [A-Z_]+[A-z\(\):, ]*")


