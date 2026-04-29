from flask import Blueprint, render_template, redirect, request, session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from services.account import redirectToDashIfLoggedIn
from services.database import db, User
from services.enums import Role
from sqlalchemy import select

accountBP = Blueprint(
    "account", __name__, static_folder="../static", template_folder="../templates"
)
ph = PasswordHasher()


@accountBP.route("/log-out", methods=["POST"])
def logout():
    """
    Clear user session cache. Log out of account.

    Returns:
        _type_: Redirect to login page.
    """
    session.pop("userId", None)
    return redirect("/login")


@accountBP.route("/login", methods=["GET", "POST"])
@redirectToDashIfLoggedIn
def login():
    """
    POST: Handle a form post request of user credentials to Log In.
    GET: Load login HTML.
    """
    if request.method == "POST":
        email = request.form.get("email_input", "").strip()
        password = request.form.get("password_input", "").strip()

        # Validate email exists in database
        user = db.session.scalar(select(User).where(User.email == email))
        if user is None:
            return "<p class='text-danger'>ERROR: Email or password is incorrect.</p>"

        # Validate password is correct
        try:
            ph.verify(user.hashedPassword, password)
        except VerifyMismatchError:
            return "<p class='text-danger'>ERROR: Email or password is incorrect.</p>"

        # Save the user ID session
        session["userId"] = user.id

        return (
            "<p class='text-success'>SUCCESS: Logged into account! Redirecting...</p>"
            + render_template(
                "subpages/redirect_in_x_ms.html", url="/dashboard", delay=500
            )
        )
        # return "<p class='text-danger'>ERROR: Username already exists.</p>"
    else:
        return render_template("display_pages/login.html")


@accountBP.route("/sign-up", methods=["GET", "POST"])
@redirectToDashIfLoggedIn
def signUp():
    """
    POST: Handle a form post request of user credentials to create an account.
    GET: Load sign-up HTML.
    """
    if request.method == "POST":
        # Get sign in fields and strip white text on left and right of string
        forename = request.form.get("forename_input", "").strip()
        surname = request.form.get("surname_input", "").strip()
        email = request.form.get("email_input", "").strip()
        affiliation = request.form.get("affiliation_input", "").strip()
        password = request.form.get("password_input", "").strip()
        role = request.form.get("role_input", "").strip()

        # Ensure the forename is at least 3 characters long
        if len(forename) < 3:
            return "<p class='text-danger'>ERROR: Forename must be at least 3 characters long.</p>"

        # Ensure the surname is at least 3 characters long
        if len(surname) < 3:
            return "<p class='text-danger'>ERROR: Surname must be at least 3 characters long.</p>"

        # Ensure the email is at least 5 characters long
        if len(email) < 5:
            return "<p class='text-danger'>ERROR: Email must be at least 5 characters long.</p>"

        # Ensure the affiliation is at least 3 characters long
        if len(affiliation) < 3:
            return "<p class='text-danger'>ERROR: Affiliation must be at least 3 characters long.</p>"

        # Validate email address doesn't exist in database
        if db.session.scalar(select(User).where(User.email == email)) is not None:
            return "<p class='text-danger'>ERROR: Email already exists.</p>"

        # Ensure password is secure (has a length of 6 characters or more)
        if len(password) < 6:
            return "<p class='text-danger'>ERROR: Password must be at least 6 characters long.</p>"

        # Hash password
        hashedPassword = ph.hash(password)

        # Create new user entity and add to database
        newUser = User(
            forename=forename,
            surname=surname,
            email=email,
            affiliation=affiliation,
            hashedPassword=hashedPassword,
            role=Role.from_str(role),
        )
        db.session.add(newUser)
        db.session.commit()

        # Save the user ID session
        session["userId"] = newUser.id

        # Return successful message and redirect page to dashboard
        return (
            "<p class='text-success'>SUCCESS: Account has been registered! Redirecting...</p>"
            + render_template(
                "subpages/redirect_in_x_ms.html", url="/dashboard", delay=500
            )
        )
    else:
        return render_template("display_pages/sign_up.html")
