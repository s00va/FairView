from services.account import getLoggedInUserId
from services.database import (
    db,
    Conference,
    JoinedConference,
    Talk,
    User,
    ReviewAllocation,
)
from services.enums import Role
from sqlalchemy import select
import random


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


def allocateTalksToReviewers(conferenceIdIn: int) -> bool:
    """
    Allocates Reviews to Talks. Ensures a reviewer cannot review a talk with the same affiliation.
    Every talk must have 2 reviewers.

    Args:
        conferenceIdIn (int): The ID of the conference.

    Returns:
        bool: Flag stating whether allocation was a success or failure.
    """
    # Get the conference
    conference = getConference(conferenceIdIn)
    if conference is None:
        return False

    # Get all talks and reviewers
    allTalksStatement = (
        select(Talk, User.affiliation)
        .join(User, User.id == Talk.speakerId)
        .where(Talk.conferenceId == conference.id)
    )
    allReviewersStatement = select(User).join(
        JoinedConference,
        (User.id == JoinedConference.userId)
        & (JoinedConference.conferenceId == conference.id)
        & (User.role == Role.REVIEWER),
    )
    allTalksAndAffiliation = db.session.execute(allTalksStatement).all()
    allTalks = []
    allTalkAffiliations = []
    for talk, affiliation in allTalksAndAffiliation:
        allTalks.append(talk)
        allTalkAffiliations.append(affiliation.strip().lower())

    allReviewers = db.session.execute(allReviewersStatement).scalars().all()

    numOfTalks = len(allTalks)
    numOfAllocatedTalks = 0

    # Create an array of talks to number of reviewers to allocate
    numOfReviewersNeededForEachTalk = [2] * numOfTalks

    # For each reviewer find all the allowed talks (can't have the same affiliation)
    legalTalksForEachReviewer = []
    potentialTalkAllocations = 0
    for reviewer in allReviewers:
        legalTalksForReviewer = []
        loweredReviewerAffiliation = reviewer.affiliation.lower()
        for dex, talkAffiliation in enumerate(allTalkAffiliations):
            if loweredReviewerAffiliation != talkAffiliation:
                legalTalksForReviewer.append(dex)
                potentialTalkAllocations += 1
        legalTalksForEachReviewer.append(legalTalksForReviewer)

    # Start allocating reviews from the least number of legal talks available
    allReviewAllocations = []
    while numOfAllocatedTalks != numOfTalks * 2 and potentialTalkAllocations != 0:
        # Get a list of the reviewers with the least number of talks available
        lenOfLeastLegalTalksAvailable = 9999
        reviewersWithLeastLegalTalksAvailable = []
        for dex, legalTalksForReviewer in enumerate(legalTalksForEachReviewer):
            lenOfLegalTalksAvailable = len(legalTalksForReviewer)
            if lenOfLegalTalksAvailable == 0:
                continue
            elif lenOfLegalTalksAvailable < lenOfLeastLegalTalksAvailable:
                lenOfLeastLegalTalksAvailable = lenOfLegalTalksAvailable
                reviewersWithLeastLegalTalksAvailable = [dex]
            elif lenOfLegalTalksAvailable == lenOfLeastLegalTalksAvailable:
                reviewersWithLeastLegalTalksAvailable.append(dex)
        # Randomly pick a reviewer
        reviewerDexToAllocateTalk = random.choice(reviewersWithLeastLegalTalksAvailable)
        # Randomly pick talk
        talkDex = random.choice(legalTalksForEachReviewer[reviewerDexToAllocateTalk])
        # Allocate talk
        allReviewAllocations.append(
            ReviewAllocation(
                talkId=allTalks[talkDex].id,
                reviewerId=allReviewers[reviewerDexToAllocateTalk].id,
            )
        )
        # Remove talk from legal talks for specific reviewer
        legalTalksForEachReviewer[reviewerDexToAllocateTalk].remove(talkDex)
        potentialTalkAllocations -= 1
        # lower the number of reviewers needed for talk. If none, remove from legal talks
        numOfReviewersNeededForEachTalk[talkDex] -= 1
        if numOfReviewersNeededForEachTalk[talkDex] == 0:
            for legalTalksForReviewer in legalTalksForEachReviewer:
                if talkDex in legalTalksForReviewer:
                    legalTalksForReviewer.remove(talkDex)
                    potentialTalkAllocations -= 1
        numOfAllocatedTalks += 1

    # Check if assignment was successful
    if numOfAllocatedTalks == numOfTalks * 2:
        for allocation in allReviewAllocations:
            db.session.add(allocation)
        db.session.commit()
        return True

    return False


# TODO for another MR in the future.
def generateTalkRankings(conferenceIdIn: int):
    pass
