from flask import Flask, render_template, session
from datetime import timedelta
from blueprints.database import db, Base


app = Flask(__name__)
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
def index():
    return render_template("subpages/base.html")


if __name__ == "__main__":
    app.run(debug=True)
