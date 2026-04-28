from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum


class Role(Enum):
    NULL = 0
    SPEARKER = 1
    REVIEWIER = 2
    CONFERENCE_MANAGER = 3

    @staticmethod
    def from_str(label):
        lablelLowered = label.lower()
        if lablelLowered == "speaker":
            return Role.SPEARKER
        elif lablelLowered == "reviewer":
            return Role.REVIEWIER
        elif lablelLowered in ("conference manager", "conference_manager"):
            return Role.CONFERENCE_MANAGER
        else:
            raise NotImplementedError


class ConferenceStatus(Enum):
    OPEN = 1
    UNDER_REVIEW = 2
    TALK_SLOTS_ALLOCATED = 3
    CLOSED = 4
