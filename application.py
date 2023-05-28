import os, requests
import csv
from dotenv import load_dotenv
from flask import (
    Flask,
    session,
    render_template,
    url_for,
    flash,
    redirect,
    request,
    jsonify,
    abort,
)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from forms import RegistrationForm, LoginForm
from flask_bcrypt import Bcrypt


app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "2f217088a246a54d6da5d92c50b499df"
bcrypt = Bcrypt(app)
Session(app)

# Set up database
dbUrl = os.getenv("DATABASE_URL")
if dbUrl[8] == ":":
    dbUrl = dbUrl[0:8] + "ql" + dbUrl[8 : len(dbUrl)]
engine = create_engine(dbUrl)
db = scoped_session(sessionmaker(bind=engine))

## Helpers


def getData(feedbackid=0):
    data = {}
    result = db.execute(
        "SELECT * from feedbacks WHERE id = :feedbackid", {"feedbackid": feedbackid}
    ).fetchone()
    print(result)
    if result:
        data["id"] = result.id
        data["title"] = result.title
        data["content"] = result.content
        data["author"] = result.user_id
        data["timestamp"] = result.timestamp
        data["attachement"] = result.attachment
    else:
        flash(f"Invalid feedback id", "danger")
    return data


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ("logged_in" not in session) or (session["logged_in"] == False):
            next = request.url
            return redirect(url_for("login", next=next))
        return f(*args, **kwargs)

    return decorated_function


def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ("logged_in" in session) and (session["logged_in"] == True):
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login"))

    if session["role"] == "admin":
        feedbacks = db.execute(
            "SELECT * from feedbacks ORDER BY timestamp DESC LIMIT 10"
        )
    else:
        feedbacks = db.execute(
            "SELECT * from feedbacks WHERE user_id = :user_id ORDER BY timestamp DESC LIMIT 10",
            {"user_id": session["user_id"]},
        )
    if request.method == "GET":
        return render_template("home.html", feedbacks=feedbacks)
    else:
        query = request.form.get("input-search")
        if query is None:
            flash(f"Search field can not be empty", "danger")
            return render_template("home.html", feedbacks=feedbacks)

        try:
            if session["role"] == "moderator":
                result = db.execute(
                    "SELECT * FROM feedbacks WHERE LOWER(content) LIKE :query OR LOWER(title) LIKE :query ",
                    {"query": "%" + query.lower() + "%"},
                ).fetchall()
            else:
                result = db.execute(
                    "SELECT * FROM feedbacks WHERE user_id = :user_id AND (LOWER(content) LIKE :query OR LOWER(title) LIKE :query) ",
                    {"user_id": session["user_id"], "query": "%" + query.lower() + "%"},
                ).fetchall()
        except Exception as e:
            print(e)
            flash(f"Connection Error", "warning")
            return render_template("home.html", feedbacks=feedbacks)

        if not result:
            return render_template(
                "list.html", result=result, feedback_not_found=True, key=query
            )

        return render_template("list.html", result=result, key=query)


@app.route("/register", methods=["GET", "POST"])
@logout_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        next_url = form.next.data
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
                {
                    "username": form.username.data,
                    "email": form.email.data,
                    "password": hashed_password,
                },
            )
            flash(f"Account created for {form.username.data}!", "success")
            db.commit()

        except Exception as e:
            print(e)
            flash(f"Account not created!", "danger")

        return redirect(url_for("login", next=next_url))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
@logout_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            next_url = form.next.data
            Q = db.execute(
                "SELECT * FROM users WHERE email LIKE :email",
                {"email": form.email.data},
            ).fetchone()

            # User exists ?
            if Q is None:
                flash(f"User does not exists", "danger")
            # Valid password ?
            elif not (Q and bcrypt.check_password_hash(Q.password, form.password.data)):
                flash(f"Invalid Login", "danger")
            else:
                # check if user is an admin
                admin = db.execute(
                    "SELECT * FROM admin WHERE username LIKE :username",
                    {"username": form.email.data},
                ).fetchone()
                if admin is not None:
                    session["role"] = "admin"
                else:
                    session["role"] = "user"

                flash(f"Logged in successfully", "success")
                session["user_id"] = Q.id
                session["email"] = Q.email
                session["username"] = Q.username
                session["logged_in"] = True

                if next_url:
                    return redirect(next_url)

        except Exception as e:
            flash(f"Connection Error {e}", "warning")

        return redirect(url_for("home"))

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html", form=form)


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        # Assuming you're getting the user_id from the session
        user_id = session.get("user_id")

        # Insert the new feedback into the database
        db.execute(
            "INSERT INTO feedbacks (title, content, user_id) VALUES (:title, :content, :user_id)",
            {"title": title, "content": content, "user_id": user_id},
        )
        db.commit()

        # Redirect the user to dashboard page after successfully posting feedback
        flash(f"Feedback submitted!", "success")
        return redirect(url_for("home"))

    # Render the feedback form page if it's a GET request or if the form data is invalid
    return render_template("feedback.html")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    session["logged_in"] = False

    # Redirect user to login index
    return redirect(url_for("home"))


@app.route("/details/<int:feedbackid>", methods=["GET", "POST"])
@login_required
def details(feedbackid):
    data = getData(feedbackid)
    if not ("comments" in data):
        data["comments"] = []
    return render_template("details.html", feedback=data, feedbackid=feedbackid)


@app.route("/del_feedback/<int:feedbackid>")
@login_required
def del_review(feedbackid):
    db.execute("DELETE from feedbacks WHERE id = :id", {"id": feedbackid})
    db.commit()
    return redirect(url_for("details", feedbackid=feedbackid))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
