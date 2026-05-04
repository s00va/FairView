from services.account import getLoggedInUserId
from services.database import Conference, ReviewAllocation, Talk, Review, db
from sqlalchemy import select, exists, not_, join


def getMyReviews(conferenceIdIn: int | None = None):
    """
    Generate custom table combining all reviews the logged in user has been allocated,
    with data about the talks and conferences it is linked to.

    Args:
        conferenceIdIn (int | None, optional): Specifies specific conference to filter reviews. Defaults to None.

    Returns:
        _type_: Table of allocated reviews.
    """
    needsReviewing = not_(
        exists().where(ReviewAllocation.id == Review.reviewAllocationId)
    ).label("needsReviewing")

    statement = (
        select(
            Talk.title.label("talkTitle"),
            Conference.title.label("conferenceTitle"),
            Conference.conferenceDate.label("conferenceDate"),
            Conference.status.label("conferenceStatus"),
            ReviewAllocation.id.label("allocationId"),
            needsReviewing,
        )
        .join(ReviewAllocation, ReviewAllocation.talkId == Talk.id)
        .join(Conference, Conference.id == Talk.conferenceId)
        .where(ReviewAllocation.reviewerId == getLoggedInUserId())
    )

    if conferenceIdIn is not None:
        statement = statement.where(Conference.id == conferenceIdIn)

    return db.session.execute(statement).all()


def getTalkTitleDescriptionAndConferenceFromReviewAllocation(
    reviewAllocationIdIn: int,
) -> None | tuple[str, str, str]:
    """
    Get Talk Title&Description, and conference relating to reviewAllocation.

    Args:
        reviewAllocationIdIn (int): Target reviewAllocation

    Returns:
        None | tuple[str, str, str]: Either found the data related to reviewAllocation or None if not found.
    """
    statement = (
        select(
            Talk.title.label("talkTitle"),
            Talk.description.label("talkDescription"),
            Conference.title.label("conference"),
        )
        .join(ReviewAllocation, ReviewAllocation.talkId == Talk.id)
        .join(Conference, Conference.id == Talk.conferenceId)
        .where(ReviewAllocation.id == reviewAllocationIdIn)
    )
    result = db.session.execute(statement).first()

    # Check if there is a result
    if result is None:
        return None

    return (result.talkTitle, result.talkDescription, result.conference)


def canUserReview(reviewAllocationIdIn: int) -> bool:
    """
    Checks if logged in user can make a review for specific allocation.

    Args:
        reviewAllocationIdIn (int): Target review allocation.

    Returns:
        bool: Flag determines whether user can review.
    """
    # Validate logged in user is meant to review
    if (
        db.session.scalar(
            select(ReviewAllocation).where(
                (ReviewAllocation.reviewerId == getLoggedInUserId())
                & (ReviewAllocation.id == reviewAllocationIdIn)
            )
        )
        is None
    ):
        return False

    # Check if a review has already been made
    return (
        db.session.scalar(
            select(Review)
            .join(ReviewAllocation, ReviewAllocation.id == Review.reviewAllocationId)
            .where(
                (ReviewAllocation.reviewerId == getLoggedInUserId())
                & (ReviewAllocation.id == reviewAllocationIdIn)
            )
        )
        is None
    )
