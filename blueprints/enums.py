from enum import Enum


class Role(Enum):
    NULL = 0
    SPEAKER = 1
    REVIEWER = 2
    CONFERENCE_MANAGER = 3

    @staticmethod
    def from_str(label):
        labelLowered = label.lower()
        if labelLowered == "speaker":
            return Role.SPEAKER
        elif labelLowered == "reviewer":
            return Role.REVIEWER
        elif labelLowered in ("conference manager", "conference_manager"):
            return Role.CONFERENCE_MANAGER
        else:
            raise NotImplementedError


class ConferenceStatus(Enum):
    OPEN = 1
    UNDER_REVIEW = 2
    TALK_SLOTS_ALLOCATED = 3
    CLOSED = 4
