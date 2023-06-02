import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_security import (Security, SQLAlchemyUserDatastore, auth_required,
                            current_user, roles_required)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func
from werkzeug.utils import secure_filename

from flask_session import Session
from forms import ExtendedRegisterForm, FeedbackForm
from models import init_models

app = Flask(__name__)

# Configure session to use filesystem
app.config["SECURITY_URL_PREFIX"] = "/"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECURITY_PASSWORD_SALT"] = "my_precious_two"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SECURITY_REGISTERABLE"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# absolute path to the directory that will hold the uploaded files
UPLOAD_FOLDER = os.path.abspath(os.getcwd()) + "/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create the directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


db = SQLAlchemy(app)


migrate = Migrate(app, db)
User, Feedback, Role = init_models(db)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)
Session(app)

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@auth_required("session")
def home():
    if current_user.has_role("admin"):
        feedbacks = (
            db.session.query(Feedback)
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
            lower_query = "%{}%".format(query.lower())
            if current_user.role == "admin":
                result = (
                    db.session.query(Feedback)
                    .filter(
                        func.lower(Feedback.content).like(lower_query)
                        | func.lower(Feedback.title).like(lower_query)
                    )
                    .all()
                )
            else:
                result = (
                    db.session.query(Feedback)
                    .filter(
                        Feedback.user_id == current_user.id,
                        (
                            func.lower(Feedback.content).like(lower_query)
                            | func.lower(Feedback.title).like(lower_query)
                        ),
                    )
                    .all()
                )
        except Exception as e:
            flash(f"Connection Error: {str(e)}", "warning")
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
    form = FeedbackForm(request.form)
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
        if form.validate():
            title = form.title.data
            content = form.content.data
            user_id = current_user.id
            file = request.files.get("attachment")
            filename = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            else:
                flash(
                    "File not allowed. Please upload a file of type: txt, pdf, png, jpg, jpeg, or gif.",
                    "error",
                )
                return redirect(request.url)
            if feedback_id and feedback:
                # Update the existing feedback
                feedback.title = title
                feedback.content = content
                feedback.attachment = filename
                flash("Feedback updated!", "success")

            else:
                # Insert the new feedback
                new_feedback = Feedback(
                    title=title, content=content, user_id=user_id, attachment=filename
                )
                db.session.add(new_feedback)
                flash("Feedback submitted!", "success")

            db.session.commit()
            return redirect(url_for("home"))

    return render_template("feedback.html", feedback=feedback)


@app.route("/mark_reviewed/<int:feedback_id>", methods=["POST"])
@roles_required(
    "admin"
)  # ensure only users with the 'admin' role can access this route
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
    if feedback is None:
        flash("Feedback not found.", "error")
    if feedback.user_id != current_user.id and not (current_user.has_role("admin")):
        flash("Access denied", "error")

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


@app.route("/disable_user/<int:user_id>", methods=["POST", "GET"])
@roles_required(
    "admin"
)  # ensure only users with the 'admin' role can access this route
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
