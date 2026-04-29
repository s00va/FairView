from flask import Blueprint, render_template, redirect, request
from blueprints.database import db, Conference, Role, JoinedConference
from blueprints.account import (
    redirectToLoginIfNotLoggedIn,
    getUserRole,
    getCurrentUser,
    getInvertedName,
    getLoggedInUserId,
    getNavbarLink,
)
from blueprints.enums import ConferenceStatus
from sqlalchemy import select
from datetime import datetime

conferenceBP = Blueprint(
    "conference", __name__, static_folder="../static", template_folder="../templates"
)


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


@conferenceBP.route("/create-conference", methods=["GET", "POST"])
@redirectToLoginIfNotLoggedIn
def createConference():
    """
    POST: Handles a form post request of necessary information to create a new conference.
    GET: Load 'Create Conference' HTML.
    """
    if request.method == "POST":
        title = request.form.get("title_input", "").strip()
        description = request.form.get("description_input", "").strip()
        slotsStr = request.form.get("slots_input", "").strip()
        conferenceDateStr = request.form.get("conferenceDate_input", "").strip()
        submissionDeadlineStr = request.form.get("submissionDeadline_input", "").strip()

        # Ensure the title is at least 3 characters long
        if len(title) < 3:
            return "<p class='text-danger'>ERROR: Title must be at least 3 characters long.</p>"

        # Ensure the description is at least 1 character long
        if len(description) < 1:
            return "<p class='text-danger'>ERROR: Description must be at least 1 characters long.</p>"

        # Attempt to convert conferenceDate into datetime format. This will fail if the passed string is incorrect or empty
        try:
            conferenceDate = datetime.fromisoformat(conferenceDateStr)
        except ValueError:
            return "<p class='text-danger'>ERROR: Conference date is not defined.</p>"

        # Attempt to convert submissionDeadline into datetime format. This will fail if the passed string is incorrect or empty
        try:
            submissionDeadline = datetime.fromisoformat(submissionDeadlineStr)
        except ValueError:
            return (
                "<p class='text-danger'>ERROR: Submission deadline is not defined.</p>"
            )

        # Attempt to convert slots into int format. This will fail if the passed string is incorrect or empty
        try:
            slots = int(slotsStr)
        except ValueError:
            return "<p class='text-danger'>ERROR: Slots is not defined.</p>"

        # Slots should be 1 or greater
        if slots <= 0:
            return "<p class='text-danger'>ERROR: Slots must be 1 or greater.</p>"

        # Get the user
        conferenceManagerUser = getCurrentUser()
        if conferenceManagerUser is None:
            return "<p class='text-danger'>ERROR: Having issues with user account information. Please refresh.</p>"

        # Create conference and add to database
        newConference = Conference(
            conferenceManagerId=conferenceManagerUser.id,
            title=title,
            description=description,
            talkSlots=slots,
            status=ConferenceStatus.OPEN,
            submissionDeadline=submissionDeadline,
            conferenceDate=conferenceDate,
        )
        db.session.add(newConference)
        db.session.commit()

        # Return successful message and redirect page to dashboard
        return (
            "<p class='text-success'>SUCCESS: Conference has been created! Redirecting...</p>"
            + render_template(
                "subpages/redirect_in_x_ms.html", url="/dashboard", delay=500
            )
        )
    else:
        # Get user role
        role = getUserRole()
        # Redirect to dashboard if not Conference Manager
        if role != Role.CONFERENCE_MANAGER:
            return redirect("/dashboard")
        return render_template("/display_pages/create_conference.html")


@conferenceBP.route("/conferences", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def searchConferences():
    """
    Returns html to display a list of every conference. Have the ability to join or manage conferences.

    Returns:
        _type_: HTML of conferences page.
    """
    # Get user role
    role = getUserRole()
    # Redirect to dashboard if not Reviewer or Speaker
    if role not in [Role.SPEAKER, Role.REVIEWER]:
        return redirect("/dashboard")

    return render_template(
        "/display_pages/search_conferences.html",
        navbarLink=getNavbarLink(),
        invertedName=getInvertedName(),
        conferenceTable_data=getAllConferencesAndIfUserHasJoined(),
        conferenceTable_title="All Conferences",
        conferenceStatus=ConferenceStatus,
        conferenceTable_showJoined=True,
    )


@conferenceBP.route("/manage-conference/<conferenceIdIn>", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def manageConference(conferenceIdIn: str):
    """
    Provide renderable HTML to manage actions for a specific conference.
    This includes viewing general details of a conference for all roles.

    Args:
        conferenceIdIn (str): Individual path segment. Specifies the conference to manage.

    Returns:
        _type_: Renderable HTML.
    """
    # Attempt to convert conferenceIdIn into int
    try:
        conferenceId = int(conferenceIdIn)
    except ValueError:
        return redirect("/dashboard")

    # Validate conferenceIdIn is a real conference
    conference = getConference(conferenceId)

    if conference is None:
        return redirect("/dashboard")

    # If the user is a speaker or reviewer, check if they have joined the conference. If not, join the conference.
    role = getUserRole()
    if role in [Role.SPEAKER, Role.REVIEWER]:
        if (
            db.session.scalar(
                select(JoinedConference).where(
                    (JoinedConference.conferenceId == conferenceId)
                    & (JoinedConference.userId == getLoggedInUserId())
                )
            )
            is None
        ):
            # Join the conference
            newJoinedConference = JoinedConference(
                userId=getLoggedInUserId(), conferenceId=conferenceId
            )
            db.session.add(newJoinedConference)
            db.session.commit()
            # Refresh page
            return redirect(request.url)

            # return f"<h1>TESTING {conferenceIdIn}</h1>"

    templateToShow = "display_pages/error.html"
    match role:
        case Role.SPEAKER:
            templateToShow = "/display_pages/manage_conference_speaker.html"
        case Role.REVIEWER:
            templateToShow = "/display_pages/manage_conference_reviewer.html"
        case Role.CONFERENCE_MANAGER:
            templateToShow = "/display_pages/manage_conference_conference_manager.html"

    return render_template(
        templateToShow,
        navbarLink=getNavbarLink(),
        invertedName=getInvertedName(),
        conference=conference,
        conferenceStatus=ConferenceStatus,
    )
