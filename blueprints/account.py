from flask import Blueprint, render_template, redirect, request, session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from blueprints.database import db, User, Role
from sqlalchemy import select
from functools import wraps

accountBP = Blueprint(
    "account", __name__, static_folder="../static", template_folder="../templates"
)
ph = PasswordHasher()


def getLoggedInUserId() -> int | None:
    """
    Return the Id of the logged in User. This can be None if not defined

    Returns:
        int | None: The logged in UserID or None.
    """
    userIdStr = session.get("userId", None)
    if userIdStr is None:
        return None
    # Try and parse ID as integer to validate.
    try:
        return int(userIdStr)
    except ValueError:
        return None


def validateUserLoggedIn() -> bool:
    """
    Checks for a valid user ID in session. This proves that the user is logged in.

    Returns:
        bool: Stating whether the user is logged in.
    """
    # Check for a userId session
    if "userId" in session:
        # Validate ID is a real value
        if getCurrentUser() is not None:
            return True
    return False


def getCurrentUser() -> User | None:
    """
    If a user is saved in session/logged in, return the user details.

    Returns:
        User | None: User details. Or None if no user is logged in.
    """
    return db.session.scalar(select(User).where(User.id == getLoggedInUserId()))


def getInvertedName() -> str:
    """
    Get inverted name of logged in user. EG Dylan, B

    Returns:
        str: Inverted name
    """
    currentUser = getCurrentUser()
    if currentUser is None:
        return ""
    return f"{currentUser.surname}, {currentUser.forename[0]}"


def getUserRole() -> Role:
    """
    Get the role of the logged in user.

    Returns:
        Role: Role of the logged in user.
    """
    user = getCurrentUser()
    if user is None:
        return Role.NULL
    else:
        return user.role


def redirectToDashIfLoggedIn(funcIn):
    """
    Wrapper designed to redirect a user to the dashboard page if already logged in.

    Args:
        funcIn (_type_): Incoming function which uses this wrapper.

    Returns:
        _type_: Either call the function as usual or redirect.
    """

    @wraps(funcIn)
    def wrapper(*args, **kwargs):
        if validateUserLoggedIn():
            return redirect("/dashboard")
        return funcIn(*args, **kwargs)

    return wrapper


def redirectToLoginIfNotLoggedIn(funcIn):
    """
    Wrapper designed to redirect a user to the login page if not logged in.

    Args:
        funcIn (_type_): Incoming function which uses this wrapper.

    Returns:
        _type_: Either call the function as usual or redirect.
    """

    @wraps(funcIn)
    def wrapper(*args, **kwargs):
        if not validateUserLoggedIn():
            return redirect("/login")
        return funcIn(*args, **kwargs)

    return wrapper


def getNavbarLink() -> str | None:
    """
    Get the required navbar link based upon the role of the user. If the user is not logged in, return None.

    Returns:
        str | None: The link of the required navbar for the logged in user.
    """

    role = getUserRole()
    match role:
        case Role.SPEAKER:
            return "subpages/navbar_speaker.html"
        case Role.REVIEWER:
            return "subpages/navbar_reviewer.html"
        case Role.CONFERENCE_MANAGER:
            return "subpages/navbar_conference_manager.html"
    return None


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
