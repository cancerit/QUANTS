import enum


class OligoCasing(enum.Enum):
    UPPER = "upper"
    LOWER = "lower"
    NONE = "unknown"


class NameAndSequenceArgs(enum.Enum):
    HEADER = "header"
    INDEX = "index"
    MIXED = "mixed"
    NONE = "none"
