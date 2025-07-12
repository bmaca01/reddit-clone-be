import enum

class AccountType(enum.Enum):
    REGULAR = 'regular'
    ADMIN = 'admin'
    SUPERUSER = 'superuser'

class VoteDirection(enum.Enum):
    UP = 'up'
    DOWN = 'down'
    NONE = 'none'