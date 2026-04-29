from services.database import db, User
from services.enums import Role
from sqlalchemy import select
from flask import session
from functools import wraps
from flask import redirect


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
