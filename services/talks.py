from services.account import getLoggedInUserId, getInvertedName
from services.database import db, Conference, TalkResult, Talk, User
from services.enums import TalkStatus, ConferenceStatus
from sqlalchemy import select, case, func, asc


def getMyTalks(conferenceIdIn: int | None = None):
    """
    Generate a custom combined table of talks and conference created by the logged in user.
    If a conference is specified, filter the results to be related to the target conference.

    Args:
        conferenceIdIn (int | None, optional): _description_. Defaults to None.

    Returns:
        _type_: Output table of combined talk and conference data.
    """

    # Define a condition for talk status
    talkStatus = case(
        (
            Conference.status == ConferenceStatus.OPEN,
            TalkStatus.SUBMITTED.name,
        ),
        (
            Conference.status == ConferenceStatus.UNDER_REVIEW,
            TalkStatus.UNDER_REVIEW.name,
        ),
        (
            (Conference.status == ConferenceStatus.TALK_SLOTS_ALLOCATED)
            & (TalkResult.selected),
            TalkStatus.ACCEPTED.name,
        ),
        (
            (Conference.status == ConferenceStatus.TALK_SLOTS_ALLOCATED)
            & (TalkResult.selected.is_(False)),
            TalkStatus.REJECTED.name,
        ),
        else_=None,
    ).label("talkStatus")

    statement = (
        select(
            Talk.title.label("talkTitle"),
            Talk.createdDate.label("talkCreatedDate"),
            Talk.id.label("id"),
            Conference.title.label("conferenceTitle"),
            Conference.submissionDeadline.label("submissionDeadline"),
            Conference.conferenceDate.label("conferenceDate"),
            talkStatus,
            TalkResult.selected.label("tmpSelected"),
            Conference.status.label("tmpStatus"),
        )
        .join(Conference, Talk.conferenceId == Conference.id)
        .outerjoin(TalkResult, Talk.id == TalkResult.talkId)
        .where(Talk.speakerId == getLoggedInUserId())
    )

    if conferenceIdIn is not None:
        statement = statement.where(Conference.id == conferenceIdIn)

    return db.session.execute(statement).all()


def getAllTalksInConference(conferenceIdIn: int):
    """
    Get all talk submissions & outcomes in regards to a specific conference.
    This is for table_conference_talk_results.html

    Args:
        conferenceIdIn (int): The specific conference.
    """
    # Define a condition for talk status
    talkStatus = case(
        (
            TalkResult.selected,
            TalkStatus.ACCEPTED.name,
        ),
        (
            TalkResult.selected.is_(False),
            TalkStatus.REJECTED.name,
        ),
        else_=None,
    ).label("talkStatus")

    name = (User.surname + ", " + func.substr(User.forename, 1, 1)).label("speakerName")

    statement = (
        select(
            Talk.title.label("talkTitle"),
            name,
            User.email.label("speakerEmail"),
            User.affiliation.label("speakerAffiliation"),
            talkStatus,
        )
        .join(Talk, Talk.speakerId == User.id)
        .join(TalkResult, TalkResult.talkId == Talk.id)
        .where(Talk.conferenceId == conferenceIdIn)
        .order_by(asc(TalkResult.rankPosition))
    )

    return db.session.execute(statement).all()
