from flask import Blueprint, render_template, redirect, request, session
from blueprints.database import db, User, Role
from blueprints.account import redirectToLoginIfNotLoggedIn, getUserRole
from sqlalchemy import select
from functools import wraps

dashboardBP = Blueprint(
    "dashboard", __name__, static_folder="../static", template_folder="../templates"
)


@dashboardBP.route("/dashboard", methods=["GET"])
@dashboardBP.route("/", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def dashboard():
    # Get user role
    role = getUserRole()
    match role:
        case Role.SPEARKER:
            return render_template("display_pages/dashboard_speaker.html")
        case Role.REVIEWIER:
            return render_template("display_pages/dashboard_reviewer.html")
        case Role.CONFERENCE_MANAGER:
            return render_template("display_pages/dashboard_conference_manager.html")
    return render_template("display_pages/error.html")
