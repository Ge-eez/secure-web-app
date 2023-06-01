import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_security import (Security, SQLAlchemyUserDatastore, auth_required,
                            current_user, roles_required)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func

from flask_session import Session
from forms import ExtendedRegisterForm

app = Flask(__name__)

# Configure session to use filesystem
app.config["SECURITY_URL_PREFIX"] = "/"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECURITY_PASSWORD_SALT"] = "my_precious_two"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SECURITY_REGISTERABLE"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")


db = SQLAlchemy(app)


migrate = Migrate(app, db)
from models import Feedback, Role, User

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)
Session(app)


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@auth_required("session")
def home():
    if current_user.has_role("admin"):
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
            .filter(Feedback.user_id == current_user.id)
            .order_by(desc(Feedback.timestamp))
            .all()
        )

    if request.method == "GET":
        return render_template("home.html", feedbacks=feedbacks)
    else:
        query = request.form.get("input-search")
        if query is None:
            flash(f"Search field can not be empty", "danger")
            return render_template("home.html", feedbacks=feedbacks)

        try:
            if current_user.role == "admin":
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
                        Feedback.user_id == current_user.id,
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


@app.route("/moderator")
@roles_required(
    "admin"
)  # ensure only users with the 'admin' role can access this route
def moderator():
    users = User.query.all()  # replace with your actual query to get all users
    return render_template("moderator.html", users=users)


@app.route("/feedback", methods=["GET", "POST"])
@app.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
@auth_required("session")
def feedback(feedback_id=None):
    feedback = None
    if feedback_id:
        feedback = (
            db.session.query(Feedback)
            .join(User)
            .filter(Feedback.user_id == current_user.id, Feedback.id == feedback_id)
            .order_by(desc(Feedback.timestamp))
            .first()
        )
        if not feedback:
            flash("Feedback not found.", "error")
            return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        user_id = current_user.id

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


@app.route("/mark_reviewed/<int:feedback_id>", methods=["POST"])
@auth_required("session")
@roles_required("admin")
def mark_reviewed(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if feedback:
        feedback.reviewed = True
        feedback.review_timestamp = datetime.now()  # don't forget to import datetime
        db.session.commit()
        flash("Feedback marked as reviewed!", "success")
    else:
        flash("Feedback not found.", "error")
    return redirect(url_for("details", feedback_id=feedback_id))


@app.route("/details/<int:feedback_id>", methods=["GET"])
@auth_required("session")
def details(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if feedback is None or feedback.user_id != current_user.id:
        flash("Feedback not found.", "error")
        return redirect(url_for("home"))

    return render_template("details.html", feedback=feedback, feedback_id=feedback_id)


@app.route("/del_feedback/<int:feedback_id>", methods=["POST"])
@auth_required("session")
def del_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if feedback is None or feedback.user_id != current_user.id:
        flash("Feedback not found.", "error")
        return redirect(url_for("home"))
    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback deleted successfully!", "success")
    return redirect(
        url_for("home")
    )  # Change this to your desired route after deleting feedback


@app.route("/disable_user/<int:user_id>", methods=["POST"])
@auth_required("session")
@roles_required("admin")
def disable_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.active = False
        db.session.commit()
        flash(f"User {user.username} disabled successfully!", "success")
    else:
        flash("User not found.", "error")
    return redirect(url_for("moderator"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
