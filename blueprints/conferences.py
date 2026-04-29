from flask import Blueprint, render_template, redirect, request, session
from blueprints.database import db, Conference, Role, JoinedConference
from blueprints.account import redirectToLoginIfNotLoggedIn, getUserRole, getCurrentUser
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
        .where(JoinedConference.userId == session["userId"])
    )
    return db.session.execute(statement).scalars().all()


def getUserCreatedConferences():
    """
    Find all conferences which the logged in user has created the conference.

    Returns:
        _type_: Array of conferences.
    """
    statement = select(Conference).where(
        Conference.conferenceManagerId == session["userId"]
    )
    return db.session.execute(statement).scalars().all()


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

        # Ensure the description is at least 10 character long
        if len(description) < 10:
            return "<p class='text-danger'>ERROR: Description must be at least 10 characters long.</p>"

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
