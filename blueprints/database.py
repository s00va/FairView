from flask import Flask
from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy import select, ForeignKey, Enum as SQLAlchemyEnum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, UTC
from blueprints.enums import Role, ConferenceStatus

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    forename: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    affiliation: Mapped[str] = mapped_column(String(250), nullable=False)
    hashedPassword: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[Role] = mapped_column(SQLAlchemyEnum(Role), nullable=False)

    talks: Mapped[list["Talk"]] = relationship(back_populates="speaker")
    conferences: Mapped[list["Conference"]] = relationship(
        back_populates="conferenceManager"
    )
    reviewAllocations: Mapped[list["ReviewAllocation"]] = relationship(
        back_populates="reviewer"
    )


class Conference(Base):
    __tablename__ = "conference"

    id: Mapped[int] = mapped_column(primary_key=True)
    conferenceManagerId: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    talkSlots: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ConferenceStatus] = mapped_column(
        SQLAlchemyEnum(ConferenceStatus), nullable=False
    )
    submissionDeadline: Mapped[datetime] = mapped_column(nullable=False)
    conferenceDate: Mapped[datetime] = mapped_column(nullable=False)
    createdDate: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    lastEdited: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    conferenceManager: Mapped["User"] = relationship(back_populates="conferences")


class Talk(Base):
    __tablename__ = "talk"

    id: Mapped[int] = mapped_column(primary_key=True)
    speakerId: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    createdDate: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    lastEdited: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    speaker: Mapped["User"] = relationship(back_populates="talks")
    reviewAllocations: Mapped[list["ReviewAllocation"]] = relationship(
        back_populates="talk"
    )
    talkResult: Mapped["TalkResult"] = relationship(
        back_populates="talk", uselist=False
    )


class ReviewAllocation(Base):
    __tablename__ = "reviewAllocation"

    id: Mapped[int] = mapped_column(primary_key=True)
    talkID: Mapped[int] = mapped_column(ForeignKey("talk.id"), nullable=False)
    reviewerId: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    talk: Mapped["Talk"] = relationship(back_populates="reviewAllocations")
    reviewer: Mapped["User"] = relationship(back_populates="reviewAllocations")
    review: Mapped["Review"] = relationship(
        back_populates="reviewAllocation", uselist=False
    )


class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)
    reviewAllocationID: Mapped[int] = mapped_column(
        ForeignKey("reviewAllocation.id"), unique=True, nullable=False
    )
    feedback: Mapped[str] = mapped_column(String(250), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    createdDate: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    lastEdited: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    reviewAllocation: Mapped["ReviewAllocation"] = relationship(back_populates="review")


class TalkResult(Base):
    __tablename__ = "talkResult"

    id: Mapped[int] = mapped_column(primary_key=True)
    talkID: Mapped[int] = mapped_column(
        ForeignKey("talk.id"), unique=True, nullable=False
    )
    rankPosition: Mapped[int] = mapped_column(nullable=False)
    selected: Mapped[bool] = mapped_column(nullable=False)
    isTieBreakApplied: Mapped[bool] = mapped_column(nullable=False)

    talk: Mapped["Talk"] = relationship(back_populates="talkResult", uselist=False)
