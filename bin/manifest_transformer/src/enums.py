import enum
from src import constants as const


class ColumnMode(enum.Enum):
    COLUMN_NAMES = const.SUBCOMMAND__COLUMN_NAMES
    COLUMN_INDICES = const.SUBCOMMAND__COLUMN_INDICES
