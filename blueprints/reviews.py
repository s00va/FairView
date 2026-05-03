from flask import Blueprint, render_template, request, redirect
from services.account import (
    getLoggedInUserId,
    getInvertedName,
    redirectToLoginIfNotLoggedIn,
    getUserRole,
)
from services.conferences import getJoinedConferences
from services.database import (
    db,
    Conference,
    JoinedConference,
    Talk,
    ReviewAllocation,
    Review,
)
from services.enums import Role, ConferenceStatus
from services.generic_methods import getWordCount
from services.reviews import (
    getMyReviews,
    getTalkTitleDescriptionAndConferenceFromReviewAllocation,
    canUserReview,
)
from sqlalchemy import select

reviewsBP = Blueprint(
    "reviews", __name__, static_folder="../static", template_folder="../templates"
)


@reviewsBP.route("/review-talk/<reviewAllocationIdIn>", methods=["GET", "POST"])
@reviewsBP.route("/review-talk", methods=["GET", "POST"])
@redirectToLoginIfNotLoggedIn
def createReview(reviewAllocationIdIn: str = ""):
    """
    POST: Get review form. Validate database is waiting for a review from target user. Update database with new review.
    GET: Load review page HTML if database is waiting for a review from target user.

    Args:
        reviewAllocationIdIn (str, optional): The ID of review allocation. Defaults to "".

    Returns:
        _type_: _description_
    """
    if request.method == "POST":
        # Attempt to convert reviewAllocationId into int
        try:
            reviewAllocationId = int(reviewAllocationIdIn)
        except ValueError:
            return "<p class='text-danger'>ERROR: Please refresh your page.</p>"

        # Check if logged in user has permission to review.
        if not canUserReview(reviewAllocationId):
            return "<p class='text-danger'>ERROR: User doesn't have permission.</p>"

        scoreStr = request.form.get("score_input", "").strip()
        feedback = request.form.get("feedback_input", "").strip()

        # Attempt to convert score into an int
        try:
            score = int(scoreStr)
        except ValueError:
            return "<p class='text-danger'>ERROR: Invalid value for score.</p>"

        # Check score is between 1 and 10
        if score < 1 or score > 10:
            return "<p class='text-danger'>ERROR: Invalid value for score.</p>"

        # Check feedback is between 1 and 250 characters
        feedbackLen = len(feedback)
        if feedbackLen < 1 or feedbackLen > 250:
            return "<p class='text-danger'>ERROR: Feedback must be between 1 and 250 characters.</p>"

        # Create review
        newReview = Review(
            reviewAllocationId=reviewAllocationId, feedback=feedback, score=score
        )
        db.session.add(newReview)
        db.session.commit()
        # Return successful message and redirect page to dashboard
        return (
            "<p class='text-success'>SUCCESS: Review has been made! Redirecting...</p>"
            + render_template(
                "subpages/redirect_in_x_ms.html", url="/dashboard", delay=500
            )
        )

    else:
        # Attempt to convert reviewAllocationId into int
        try:
            reviewAllocationId = int(reviewAllocationIdIn)
        except ValueError:
            return redirect("/dashboard")

        # Check if logged in user has permission to review.
        if not canUserReview(reviewAllocationId):
            return redirect("/dashboard")

        # Get information in regards to review allocation to display on page
        result = getTalkTitleDescriptionAndConferenceFromReviewAllocation(
            reviewAllocationId
        )
        # Check if there was a result
        if result is None:
            return redirect("/dashboard")

        talkTitle, talkDescription, conference = result

        return render_template(
            "/display_pages/create_review.html",
            invertedName=getInvertedName(),
            talkTitle=talkTitle,
            talkDescription=talkDescription,
            conference=conference,
        )


@reviewsBP.route("/reviews", methods=["GET"])
@redirectToLoginIfNotLoggedIn
def searchReviews():
    """
    Render HTML to display a list of every review the logged in user is/has been tasked with reviewing.

    Returns:
        _type_: Rendered HTML.
    """

    # Get user role
    role = getUserRole()
    # Redirect to dashboard if not reviewer
    if role != Role.REVIEWER:
        return redirect("/dashboard")

    return render_template(
        "/display_pages/reviews.html",
        invertedName=getInvertedName(),
        reviewTable_title="Talks To Review",
        reviewTable_data=getMyReviews(),
        conferenceStatus=ConferenceStatus,
    )
