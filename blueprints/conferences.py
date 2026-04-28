from flask import Blueprint, render_template, redirect, request, session
from blueprints.database import db, User, Conference, Role, JoinedConference
from blueprints.account import redirectToLoginIfNotLoggedIn, getUserRole
from sqlalchemy import select
from functools import wraps

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


# @dashboardBP.route("/dashboard", methods=["GET"])
# @redirectToLoginIfNotLoggedIn
# def dashboard():
#     # Get user role
#     role = getUserRole()
#     match role:
#         case Role.SPEARKER:
#             return render_template(
#                 "display_pages/dashboard_speaker.html", conferences=joinedConferences
#             )
#         case Role.REVIEWIER:
#             return render_template("display_pages/dashboard_reviewer.html")
#         case Role.CONFERENCE_MANAGER:
#             return render_template("display_pages/dashboard_conference_manager.html")
#     return render_template("display_pages/error.html")
