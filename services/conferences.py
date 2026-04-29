from services.account import getLoggedInUserId
from services.database import db, Conference, JoinedConference
from sqlalchemy import select


def getJoinedConferences():
    """
    Find all conferences which the logged in user has joined.

    Returns:
        _type_: Array of conferences.
    """
    statement = (
        select(Conference)
        .join(JoinedConference, Conference.id == JoinedConference.conferenceId)
        .where(JoinedConference.userId == getLoggedInUserId())
    )
    return db.session.execute(statement).scalars().all()


def getAllConferencesAndIfUserHasJoined():
    """
    Get a list of all conferences merged with Joined Conferences. Checking if the current user has joined the conference.

    Returns:
        _type_: Array of conferences.
    """
    statement = select(
        Conference.id,
        Conference.title,
        Conference.description,
        Conference.createdDate,
        Conference.conferenceDate,
        Conference.lastEdited,
        Conference.status,
        JoinedConference.userId,
    ).outerjoin(
        JoinedConference,
        (Conference.id == JoinedConference.conferenceId)
        & (JoinedConference.userId == getLoggedInUserId()),
    )
    return db.session.execute(statement).all()


def getUserCreatedConferences():
    """
    Find all conferences which the logged in user has created the conference.

    Returns:
        _type_: Array of conferences.
    """
    statement = select(Conference).where(
        Conference.conferenceManagerId == getLoggedInUserId()
    )
    return db.session.execute(statement).scalars().all()


def getConference(conferenceIdIn: int) -> Conference | None:
    """
    Get the conference with the id of conferenceIdIn.
    If none is found return None.

    Args:
        conferenceIdIn (int): The ID of the target conference.

    Returns:
        Conference | None: The target conference or None.
    """
    return db.session.scalar(select(Conference).where(Conference.id == conferenceIdIn))
