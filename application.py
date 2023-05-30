import os
from sqlalchemy import desc, func
from flask_sqlalchemy import SQLAlchemy

from flask import Flask, session, render_template, url_for, flash, redirect, request
from flask_session import Session
from functools import wraps
from forms import RegistrationForm, LoginForm
from flask_bcrypt import Bcrypt
from datetime import datetime


app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "2f217088a246a54d6da5d92c50b499df"
bcrypt = Bcrypt(app)
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

from models import User, Feedback, Admin


def getData(feedbackid=0):
    data = {}
    feedback = Feedback.query.get(feedbackid)
    if feedback:
        data["id"] = feedback.id
        data["title"] = feedback.title
        data["content"] = feedback.content
        data["author"] = feedback.user_id
        data["timestamp"] = feedback.timestamp
        data["attachment"] = feedback.attachment
        data["reviewed"] = feedback.reviewed
        data["review_timestamp"] = feedback.review_timestamp
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
        feedbacks = (
            db.session.query(Feedback, User.username)
            .join(User)
            .order_by(desc(Feedback.timestamp))
            .all()
        )
    else:
        feedbacks = (
            db.session.query(Feedback)
            .join(User)
            .filter(Feedback.user_id == session["user_id"])
            .order_by(desc(Feedback.timestamp))
            .all()
        )

    print(feedbacks)

    if request.method == "GET":
        return render_template("home.html", feedbacks=feedbacks)
    else:
        query = request.form.get("input-search")
        if query is None:
            flash(f"Search field can not be empty", "danger")
            return render_template("home.html", feedbacks=feedbacks)

        try:
            if session["role"] == "admin":
                result = (
                    db.session.query(Feedback)
                    .filter(
                        func.lower(Feedback.content).like(f"%{query.lower()}%")
                        | func.lower(Feedback.title).like(f"%{query.lower()}%")
                    )
                    .all()
                )
            else:
                result = (
                    db.session.query(Feedback)
                    .filter(
                        Feedback.user_id == session["user_id"],
                        (
                            func.lower(Feedback.content).like(f"%{query.lower()}%")
                            | func.lower(Feedback.title).like(f"%{query.lower()}%")
                        ),
                    )
                    .all()
                )
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
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )

        try:
            db.session.add(user)
            db.session.commit()
            flash(f"Account created for {form.username.data}!", "success")

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
            user = User.query.filter_by(email=form.email.data).first()

            if user is None:
                flash(f"User does not exists", "danger")
            elif not bcrypt.check_password_hash(user.password, form.password.data):
                flash(f"Invalid Login", "danger")
            else:
                admin = Admin.query.filter_by(username=form.email.data).first()
                if admin is not None:
                    session["role"] = "admin"
                else:
                    session["role"] = "user"

                flash(f"Logged in successfully", "success")
                session["user_id"] = user.id
                session["email"] = user.email
                session["username"] = user.username
                session["logged_in"] = True

                if next_url:
                    return redirect(next_url)

        except Exception as e:
            flash(f"Connection Error {e}", "warning")

        return redirect(url_for("home"))

    return render_template("login.html", form=form)


@app.route("/feedback", methods=["GET", "POST"])
@app.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
@login_required
def feedback(feedback_id=None):
    feedback = None
    if feedback_id:
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            flash("Feedback not found.", "error")
            return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        user_id = session.get("user_id")

        if feedback_id and feedback:
            # Update the existing feedback
            feedback.title = title
            feedback.content = content
            flash("Feedback updated!", "success")
        else:
            # Insert the new feedback
            new_feedback = Feedback(title=title, content=content, user_id=user_id)
            db.session.add(new_feedback)
            flash("Feedback submitted!", "success")

        db.session.commit()
        return redirect(url_for("home"))

    return render_template("feedback.html", feedback=feedback)


@app.route("/users", methods=["GET", "POST"])
def users():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        flash(f"Unauthorized access", "danger")
        return redirect(url_for("home"))

    users = User.query.all()

    return render_template("users.html", users=users)


@app.route("/mark_reviewed/<int:feedback_id>", methods=["GET", "POST"])
@login_required
def mark_reviewed(feedback_id):
    if request.method == "POST":
        feedback = Feedback.query.get(feedback_id)
        feedback.reviewed = True
        feedback.review_timestamp = datetime.now()  # don't forget to import datetime
        db.session.commit()

        flash("Feedback marked as reviewed!", "success")
        return redirect(url_for("feedback", feedback_id=feedback_id))

    feedback = Feedback.query.get(feedback_id)
    return render_template("feedback.html", feedback=feedback)


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    session["logged_in"] = False

    # Redirect user to login index
    return redirect(url_for("home"))


@app.route("/details/<int:feedback_id>", methods=["GET", "POST"])
@login_required
def details(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if feedback is None:
        flash("Feedback not found.", "error")
        return redirect(url_for("home"))

    feedback_data = feedback.__dict__
    if "_sa_instance_state" in feedback_data:
        del feedback_data["_sa_instance_state"]
    if "comments" not in feedback_data:
        feedback_data["comments"] = []
    return render_template(
        "details.html", feedback=feedback_data, feedback_id=feedback_id
    )


@app.route("/del_feedback/<int:feedback_id>")
@login_required
def del_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if feedback is None:
        flash("Feedback not found.", "error")
        return redirect(url_for("home"))
    db.session.delete(feedback)
    db.session.commit()
    return redirect(
        url_for("home")
    )  # Change this to your desired route after deleting feedback


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
