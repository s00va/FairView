from services.account import getLoggedInUserId
from services.database import (
    db,
    Conference,
    JoinedConference,
    Talk,
    User,
    ReviewAllocation,
    Review,
    TalkResult,
)
from services.enums import Role
from sqlalchemy import select, func, desc
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

    # If there are no talks, don't allocate
    if len(allTalksAndAffiliation) == 0:
        return False

    allTalks = []
    allTalkAffiliations = []
    for talk, affiliation in allTalksAndAffiliation:
        allTalks.append(talk)
        allTalkAffiliations.append(affiliation.strip().lower())

    allReviewers = db.session.execute(allReviewersStatement).scalars().all()

    # If there are no reviewers, don't allocate
    if len(allReviewers) == 0:
        return False

    numOfTalks = len(allTalks)
    numOfAllocatedTalks = 0

    # Create an array of talks to number of reviewers to allocate
    numOfReviewersNeededForEachTalk = [2] * numOfTalks

    # Create an array of number of allocated talks for each reviewer
    numOfAllocationsForEachReviewer = [0] * len(allReviewers)

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

    # Allocate by fewest current allocations, then by fewest legal talks available.
    allReviewAllocations = []
    while numOfAllocatedTalks != numOfTalks * 2 and potentialTalkAllocations != 0:
        # Get a list of the reviewers with the number of allocated talks and the least number of talks available
        # Prioritise fair number of allocated talks then number of least talks available
        lowestScore = (9999, 9999)
        reviewersWithLowestScores = []
        for dex, legalTalksForReviewer in enumerate(legalTalksForEachReviewer):
            score = (numOfAllocationsForEachReviewer[dex], len(legalTalksForReviewer))
            if score[1] == 0:
                continue
            elif score < lowestScore:
                lowestScore = score
                reviewersWithLowestScores = [dex]
            elif score == lowestScore:
                reviewersWithLowestScores.append(dex)
        # Randomly pick a reviewer
        reviewerDexToAllocateTalk = random.choice(reviewersWithLowestScores)
        # Randomly pick talk
        talkDex = random.choice(legalTalksForEachReviewer[reviewerDexToAllocateTalk])
        # Allocate talk
        allReviewAllocations.append(
            ReviewAllocation(
                talkId=allTalks[talkDex].id,
                reviewerId=allReviewers[reviewerDexToAllocateTalk].id,
            )
        )
        numOfAllocationsForEachReviewer[reviewerDexToAllocateTalk] += 1
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


def generateTalkRankings(conferenceIdIn: int) -> bool:
    """
    Validates all reviews have been completed.
    Then sums up the scores for each talk and orders from highest to lowest.
    The highest scores fill up the conference slots.

    Args:
        conferenceIdIn (int): The specific conference.

    Returns:
        bool: Flag describing whether generate Talk Rankings was successful.
    """
    # Get the conference in mention. Check it is valid.
    conference = getConference(conferenceIdIn)
    if conference is None:
        return False

    # Check all reviews are met by checking if there are any null outer joins
    statement = (
        select(ReviewAllocation)
        .join(Talk, Talk.id == ReviewAllocation.talkId)
        .outerjoin(Review, Review.reviewAllocationId == ReviewAllocation.id)
        .where(Talk.conferenceId == conferenceIdIn, Review.id.is_(None))
        .limit(1)
    )
    # If the result is None, all reviews have been made
    if db.session.execute(statement).first() is not None:
        return False

    # Get talk id average of both scores, rank from highest to lowest score, if the same score, order randomly
    averageScore = func.avg(Review.score)
    statement = (
        select(Talk.id.label("id"), averageScore.label("averageScore"))
        .join(ReviewAllocation, ReviewAllocation.talkId == Talk.id)
        .join(Review, Review.reviewAllocationId == ReviewAllocation.id)
        .where(Talk.conferenceId == conferenceIdIn)
        .group_by(Talk.id)
        .order_by(desc(averageScore), func.random())
    )
    allTalksAndScores = db.session.execute(statement).all()

    # Get number of available slots
    slots = conference.talkSlots

    # Check if there is any tie break
    allTieBreakTalkIds = []
    if slots < len(allTalksAndScores):
        boundaryScore = allTalksAndScores[slots - 1].averageScore
        nextScore = allTalksAndScores[slots].averageScore

        if boundaryScore == nextScore:
            for talkAndScore in allTalksAndScores:
                if talkAndScore.averageScore == nextScore:
                    allTieBreakTalkIds.append(talkAndScore.id)

    # Create TalkResults
    for rank, talkAndScore in enumerate(allTalksAndScores):
        db.session.add(
            TalkResult(
                talkId=talkAndScore.id,
                rankPosition=rank + 1,
                selected=rank < slots,
                isTieBreakApplied=talkAndScore.id in allTieBreakTalkIds,
            )
        )

    db.session.commit()
    return True
