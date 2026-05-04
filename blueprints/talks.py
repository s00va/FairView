from flask import Blueprint, render_template, request, redirect
from services.account import (
    getLoggedInUserId,
    getInvertedName,
    redirectToLoginIfNotLoggedIn,
    getUserRole,
)
from services.conferences import getJoinedConferences
from services.database import db, Conference, JoinedConference, Talk
from services.enums import Role
from services.generic_methods import getWordCount
from services.talks import getMyTalks
from sqlalchemy import select

talksBP = Blueprint(
    "talks", __name__, static_folder="../static", template_folder="../templates"
)


@talksBP.route("/create-talk/<conferenceIdIn>", methods=["GET", "POST"])
@talksBP.route("/create-talk", methods=["GET", "POST"])
@redirectToLoginIfNotLoggedIn
def createTalk(conferenceIdIn: str = ""):
    """
    POST: Handle a form request to create a talk.
    GET: Load create talk html. Handle a default conference id given by url.

    Args:
        conferenceIdIn (str, optional): Override conference ID to use as default. Defaults to "".
    """
    if request.method == "POST":
        title = request.form.get("title_input", "").strip()
        description = request.form.get("description_input", "").strip()
        conference = request.form.get("conference_input", "").strip()

        # Ensure the title is at least 3 characters long
        if len(title) < 3:
            return "<p class='text-danger'>ERROR: Title must be at least 3 characters long.</p>"

        # Ensure the description is at least 1 character long
        if len(description) < 1:
            return "<p class='text-danger'>ERROR: Description must be at least 1 character long.</p>"

        # Ensure the description is 250 words max or less.
        if getWordCount(description) > 250:
            return (
                "<p class='text-danger'>ERROR: Description must be max 250 words.</p>"
            )

        # Attempt to convert conference into int.
        try:
            conferenceId = int(conference)
        except ValueError:
            return "<p class='text-danger'>ERROR: Conference error. Likely no conference selected.</p>"

        # Check if there is a joined conference with that ID.
        statement = (
            select(Conference)
            .join(JoinedConference, Conference.id == JoinedConference.conferenceId)
            .where(
                (JoinedConference.userId == getLoggedInUserId())
                & (Conference.id == conferenceId)
            )
        )
        legalConference = db.session.execute(statement).scalars().all()
        if legalConference is None:
            return "<p class='text-danger'>ERROR: Conference error. Likely no conference selected.</p>"

        newTalk = Talk(
            speakerId=getLoggedInUserId(),
            title=title,
            description=description,
            conferenceId=conferenceId,
        )
        db.session.add(newTalk)
        db.session.commit()

        # Return successful message and redirect page to dashboard
        return (
            "<p class='text-success'>SUCCESS: Talk has been created! Redirecting...</p>"
            + render_template(
                "subpages/redirect_in_x_ms.html", url="/dashboard", delay=500
            )
        )

    else:
        # Attempt to convert conferenceIdIn into int
        try:
            conferenceId = int(conferenceIdIn)
        except ValueError:
            # Will assume no conference is selected by default
            conferenceId = -1

        return render_template(
            "/display_pages/create_talk.html",
            joinedConferences=getJoinedConferences(),
            defaultConferenceId=conferenceId,
        )


@talksBP.route("/talks", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def searchTalks():
    """
    Render HTML to display a list of every talk the logged in user has created.

    Returns:
        _type_: Rendered HTML.
    """

    # Get user role
    role = getUserRole()
    # Redirect to dashboard if not Speaker
    if role != Role.SPEAKER:
        return redirect("/dashboard")

    return render_template(
        "/display_pages/talks.html",
        invertedName=getInvertedName(),
        talkTable_data=getMyTalks(),
        talkTable_title="My Talks",
        talkTable_buttonTitle="+ New Talk",
        talkTable_buttonLink="/create-talk",
    )
