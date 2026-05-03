from argon2 import PasswordHasher
import argparse
from flask import Flask
from services.database import (
    db,
    Base,
    User,
    Conference,
    Talk,
    JoinedConference,
)
from services.enums import Role, ConferenceStatus
from sqlalchemy import select
import random
import json
from datetime import datetime


def createUser(roleIn: Role):
    """
    Creates a user of a specific role.

    Args:
        roleIn (Role): Target Role of user.
    """
    # Find a unique email
    userData = None
    while userData is None:
        # Get user from json
        userData = random.choice(usersJson)
        # Validate data is of correct role
        if userData["role"] != roleIn.name:
            userData = None
            continue
        statement = select(User).where(User.email == userData["email"])
        if db.session.scalar(statement) is not None:
            userData = None

    # Create user and add to database
    newUser = User(
        forename=userData["forename"],
        surname=userData["surname"],
        email=userData["email"],
        affiliation=userData["affiliation"],
        hashedPassword=ph.hash(userData["password"]),
        role=roleIn,
    )

    print(
        f"Created User: forename={userData['forename']:<20} surname={userData['surname']:<20} email={userData['email']:<50} affiliation={userData['affiliation']:<50} password={userData['password']:<20} role={userData['role']}"
    )

    db.session.add(newUser)


def createConference():
    """
    Create a conference for a random conference manager.
    """
    # Find random conference manager
    cmStatement = select(User).where(User.role == Role.CONFERENCE_MANAGER)
    allConferenceManagers = db.session.execute(cmStatement).scalars().all()

    # Check if there are any conference managers
    if not allConferenceManagers:
        print("ERROR: No conference managers in database. Cannot create conference.")
        return

    # Get conference from json
    conference = random.choice(conferenceJson)

    # Create conference from a random conference manager and add to database
    newConference = Conference(
        conferenceManagerId=random.choice(allConferenceManagers).id,
        title=conference["title"],
        description=conference["description"],
        talkSlots=conference["talkSlots"],
        status=ConferenceStatus.OPEN,
        submissionDeadline=datetime.fromisoformat(conference["submissionDeadline"]),
        conferenceDate=datetime.fromisoformat(conference["conferenceDate"]),
    )

    print(f"Created Conference: title={conference['title']}")

    db.session.add(newConference)


def createTalk(conferenceIdIn: int):
    """
    Creates a talk from a random speaker which has joined the target conference.

    Args:
        conferenceIdIn (int): Target conference.
    """
    # Find random speaker which has joined conference
    sStatement = (
        select(User)
        .join(JoinedConference, JoinedConference.userId == User.id)
        .where(User.role == Role.SPEAKER)
    )
    allSpeakers = db.session.execute(sStatement).scalars().all()

    # Check if there are any speakers
    if not allSpeakers:
        print("ERROR: No joined speakers in database. Cannot create talks.")
        return

    # Get talk from json
    talk = random.choice(talksJson)

    # Create talk from a random speaker and add to database
    newTalk = Talk(
        speakerId=random.choice(allSpeakers).id,
        title=talk["title"],
        description=talk["description"],
        conferenceId=conferenceIdIn,
    )

    print(f"Created Talk: title={talk['title']}")

    db.session.add(newTalk)


def joinUsersToConference(roleIn: Role, conferenceIdIn: int):
    """
    Join a user of a specific role to a specific conference.

    Args:
        roleIn (Role): Target role of user.
        conferenceIdIn (int): Target conference.
    """
    # Find a user of correct role and ensure they haven't joined conference
    statement = (
        select(User)
        .outerjoin(
            JoinedConference,
            (User.id == JoinedConference.userId)
            & (JoinedConference.conferenceId == conferenceIdIn),
        )
        .where((User.role == roleIn) & (JoinedConference.id.is_(None)))
    )
    allUsers = db.session.execute(statement).scalars().all()

    # Check if any user are available.
    if not allUsers:
        print("ERROR: No available users in database to join to conference.")
        return

    # Join user to conference and add to database
    newJoinedConference = JoinedConference(
        userId=random.choice(allUsers).id,
        conferenceId=conferenceIdIn,
    )

    print(f"Joined User: type={roleIn} to conferenceId={conferenceIdIn}")

    db.session.add(newJoinedConference)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate example data for a database")

    parser.add_argument("--speakers", "-s", "-S", type=int)
    parser.add_argument("--reviewers", "-r", "-R", type=int)
    parser.add_argument("--conference_managers", "-cm", "-CM", type=int)

    parser.add_argument("--conferences", "-c", "-C", type=int)
    parser.add_argument("--talks", "-t", "-T", type=int)
    parser.add_argument("--reviews", "-re", "-RE", type=int)

    parser.add_argument("--join_speakers_to_conference", "-js", "-JS", type=int)
    parser.add_argument("--join_reviewers_to_conference", "-jr", "-JR", type=int)

    # TODO for future MR, create reviews for specific conference.

    parser.add_argument("--conference_id", "-cid", "-CID", type=int)

    args = parser.parse_args()

    # Init password hasher
    ph = PasswordHasher()

    # Init DB
    app = Flask(__name__)
    app.config |= {
        "SQLALCHEMY_ENGINES": {
            "default": "sqlite:///default.sqlite",
        },
    }
    db.init_app(app)
    with app.app_context():
        Base.metadata.create_all(db.engine)

        # Import users json
        with open("ExampleData/users_10000.json", "r") as jsonFile:
            usersJson = json.load(jsonFile)

        # Import conference json
        with open("ExampleData/conferences_1000.json", "r") as jsonFile:
            conferenceJson = json.load(jsonFile)

        # Import talks json
        with open("ExampleData/talks_1000.json", "r") as jsonFile:
            talksJson = json.load(jsonFile)

        # Import reviews json
        with open("ExampleData/reviews_1000.json", "r") as jsonFile:
            reviewsJson = json.load(jsonFile)

        # Create n speakers
        if args.speakers is not None:
            for _ in range(args.speakers):
                createUser(Role.SPEAKER)

        # Create n reviewers
        if args.reviewers is not None:
            for _ in range(args.reviewers):
                createUser(Role.REVIEWER)

        # Create n conference managers
        if args.conference_managers is not None:
            for _ in range(args.conference_managers):
                createUser(Role.CONFERENCE_MANAGER)

        # Create n conferences
        if args.conferences is not None:
            for _ in range(args.conferences):
                createConference()

        # Create n talks for specific conference
        if args.talks is not None:
            # Check if there is a specified conference
            if args.conference_id is None:
                print("ERROR: No conference ID specified for talks.")
            else:
                for _ in range(args.talks):
                    createTalk(args.conference_id)

        # Join n speakers to specific conference
        if args.join_speakers_to_conference is not None:
            if args.conference_id is None:
                print("ERROR: No conference ID specified for linking speakers.")
            else:
                for _ in range(args.join_speakers_to_conference):
                    joinUsersToConference(Role.SPEAKER, args.conference_id)

        # Join n reviewers to specific conference
        if args.join_reviewers_to_conference is not None:
            if args.conference_id is None:
                print("ERROR: No conference ID specified for linking reviewers.")
            else:
                for _ in range(args.join_reviewers_to_conference):
                    joinUsersToConference(Role.REVIEWER, args.conference_id)

        db.session.commit()
