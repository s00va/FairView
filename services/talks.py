from services.account import getLoggedInUserId
from services.database import db, Conference, TalkResult, Talk
from services.enums import TalkStatus, ConferenceStatus
from sqlalchemy import select, case


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
            & (not TalkResult.selected),
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
        )
        .join(Conference, Talk.conferenceId == Conference.id)
        .outerjoin(TalkResult, Talk.id == TalkResult.talkID)
        .where(Talk.speakerId == getLoggedInUserId())
    )

    if conferenceIdIn is not None:
        statement = statement.where(Conference.id == conferenceIdIn)

    return db.session.execute(statement).all()
