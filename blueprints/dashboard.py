from flask import Blueprint, render_template, redirect, request, session
from blueprints.database import db, User, Conference, Role, JoinedConference
from blueprints.account import (
    redirectToLoginIfNotLoggedIn,
    getUserRole,
    getInvertedName,
)
from blueprints.conferences import getJoinedConferences, getUserCreatedConferences
from blueprints.enums import ConferenceStatus
from sqlalchemy import select
from functools import wraps

dashboardBP = Blueprint(
    "dashboard", __name__, static_folder="../static", template_folder="../templates"
)


@dashboardBP.route("/dashboard", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def dashboard():
    """
    Load dashboard html. Depending on the role type, the content viewed will differ.

    Returns:
        _type_: Dashboard html to render.
    """
    # Get user role
    role = getUserRole()
    match role:
        case Role.SPEARKER:
            speakerCards = [
                dashboardCard(
                    "createTalkTemp",
                    "static/img/dashboard/new_talk_icon.png",
                    "Create New Talk",
                    "Submit a new talk to a conference",
                ),
                dashboardCard(
                    "talks",
                    "static/img/dashboard/view_talks_icon.png",
                    "Manage Talks",
                    "View and manage your existing talks",
                ),
                dashboardCard(
                    "conferences",
                    "static/img/dashboard/join_conference_icon.png",
                    "Join Conference",
                    "Discover and join new conferences",
                ),
            ]
            return render_template(
                "display_pages/dashboard.html",
                navbarLink="subpages/navbar_speaker.html",
                invertedName=getInvertedName(),
                conferenceTable_data=getJoinedConferences(),
                dashboardCards=speakerCards,
                conferenceTable_title="Joined Conferences",
                conferenceStatus=ConferenceStatus,
            )
        case Role.REVIEWIER:
            reviewerCards = [
                dashboardCard(
                    "reviews",
                    "static/img/dashboard/view_talks_icon.png",
                    "Manage Reviews",
                    "View and manage your existing reviews",
                ),
                dashboardCard(
                    "conferences",
                    "static/img/dashboard/join_conference_icon.png",
                    "Join Conference",
                    "Discover and join new conferences",
                ),
            ]
            return render_template(
                "display_pages/dashboard.html",
                navbarLink="subpages/navbar_reviewer.html",
                invertedName=getInvertedName(),
                conferenceTable_data=getJoinedConferences(),
                dashboardCards=reviewerCards,
                conferenceTable_title="Joined Conferences",
                conferenceStatus=ConferenceStatus,
            )
        case Role.CONFERENCE_MANAGER:
            conferenceManagerCards = [
                dashboardCard(
                    "create-conference",
                    "static/img/dashboard/new_talk_icon.png",
                    "Create New Conference",
                    "Create a new conference",
                )
            ]
            return render_template(
                "display_pages/dashboard.html",
                navbarLink="subpages/navbar_conference_manager.html",
                invertedName=getInvertedName(),
                conferenceTable_data=getUserCreatedConferences(),
                dashboardCards=conferenceManagerCards,
                conferenceTable_title="My Conferences",
                conferenceTable_buttonTitle="+ New Conference",
                conferenceTable_buttonLink="create-conference",
                conferenceStatus=ConferenceStatus,
                confernceTable_showLastEdited=True,
            )
    return render_template("display_pages/error.html")


class dashboardCard:
    """
    Containing information to display a single card on the dashboard.
    """

    def __init__(self, linkIn, imgIn, titleIn, descriptionIn):
        self.link = linkIn
        self.img = imgIn
        self.title = titleIn
        self.description = descriptionIn
