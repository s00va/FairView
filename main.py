from flask import Flask, redirect
from datetime import timedelta
from services.database import db, Base
from blueprints.account import accountBP
from blueprints.dashboard import dashboardBP
from blueprints.conferences import conferenceBP
from blueprints.talks import talksBP


app = Flask(__name__)
app.register_blueprint(accountBP, url_prefix="")
app.register_blueprint(dashboardBP, url_prefix="")
app.register_blueprint(conferenceBP, url_prefix="")
app.register_blueprint(talksBP, url_prefix="")
app.config |= {
    "SQLALCHEMY_ENGINES": {
        "default": "sqlite:///default.sqlite",
    },
    "PERMANENT_SESSION_LIFETIME": timedelta(days=1),
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": True,
}
app.config.from_prefixed_env()
app.secret_key = "Very Secret Key. shhhhhh..."
db.init_app(app)
with app.app_context():
    Base.metadata.create_all(db.engine)


@app.route("/")
@app.route("/home")
@app.route("/index")
def index():
    """
    Redirect to dashboard if home,index, or nothing is given as a subheader for the url.

    Returns:
        _type_: Redirect to dashboard
    """
    return redirect("dashboard")


if __name__ == "__main__":
    app.run(debug=True)
