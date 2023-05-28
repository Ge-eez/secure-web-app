import os, requests
import csv
from dotenv import load_dotenv
from flask import Flask, session, render_template, url_for, flash, redirect, request, jsonify, abort
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
app.config['SECRET_KEY'] = '2f217088a246a54d6da5d92c50b499df'
bcrypt = Bcrypt(app)
Session(app)

# Set up database
dbUrl = os.getenv("DATABASE_URL")
if(dbUrl[8] == ":"):
    dbUrl = dbUrl[0:8] + "ql" + dbUrl[8:len(dbUrl)]
engine = create_engine(dbUrl)
db = scoped_session(sessionmaker(bind=engine))

## Helpers
def getAverage(comment_list):
    average = 0

    for comment in comment_list:
        average += comment.review_score

    if(len(comment_list) > 0):
        average /= len(comment_list)
    return average

def getData(bookid=0,isbn=0):
    data = {}
    #Get book details
    if(bookid == 0):
        result = db.execute("SELECT * from books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    else:
        result = db.execute("SELECT * from books WHERE id = :id", {"id": bookid}).fetchone()
    if(result):
        data['title'] = result.title
        data['isbn'] = result.isbn
        data['author'] = result.author
        data['year'] = result.year

        #Get API data from Google API
        try:
            google = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{result.isbn}").json()
            comment_list = db.execute("SELECT u.username, u.email, u.id AS u_id, r.id as r_id, r.review_score, r.review_msg from reviews r JOIN users u ON u.id=r.users_id WHERE books_id = :id", {"id": bookid}).fetchall()
            if comment_list is None:
                comment_list = []
            if(google['totalItems'] > 0):
                data['review count'] = google["items"][0]["volumeInfo"]["ratingsCount"] + len(comment_list)
                av1 = getAverage(comment_list)
                av2 = (google["items"][0]["volumeInfo"]["averageRating"])
                av3 = av2
                if av1 > 0:
                    av3 = (av1 + av2)/2
                data['average score'] = av3
                if('imageLinks' in google["items"][0]["volumeInfo"]):
                    if('thumbnail' in google["items"][0]["volumeInfo"]["imageLinks"]):
                        data['thumbnail'] = google["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
                
            else:
                data['review count'] = len(comment_list)
                av1 = getAverage(comment_list)
                if(av1 > 0):
                    data['average score'] = av1
                else:
                    data['average score'] = "Data not available"
            data['comments'] = comment_list
        except Exception as e:
            flash(f'Connection Error', 'danger')
    else:
        flash(f'Invalid book id', 'danger')
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


@app.route("/", methods=["GET","POST"])
@app.route("/home", methods=["GET","POST"])
def home():
    books = db.execute("SELECT * from books ORDER BY random() LIMIT 10")
    if request.method == "GET":
        return render_template("home.html", books=books)
    else:
        if ("logged_in" not in session) or (session["logged_in"] == False):
            return redirect(url_for('login'))
        query = request.form.get("input-search")
        if query is None:
            flash(f'Search field can not be empty', 'danger')
        try:
            result = db.execute("SELECT * FROM books WHERE LOWER(isbn) LIKE :query OR LOWER(title) LIKE :query OR LOWER(author) LIKE :query ", {"query": "%" + query.lower() + "%"}).fetchall()
        except Exception as e:
            flash(f'Conection Error', 'warning')
            return render_template("home.html", books=books)
        if not result:
            return render_template("list.html", result=result, book_not_found=True, key=query)

        return render_template("list.html", result=result, key=query)


@app.route('/register', methods=['GET', 'POST'])
@logout_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        next_url = form.next.data
        try:
                db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
                               {"username": form.username.data, "email":form.email.data, "password": hashed_password})
                flash(f'Account created for {form.username.data}!', 'success')
                db.commit()
        
        except Exception as e:
            flash(f'Account not created!', 'danger')

        return redirect(url_for("login", next=next_url))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try: 
            next_url = form.next.data
            Q = db.execute("SELECT * FROM users WHERE email LIKE :email", {"email": form.email.data}).fetchone()

            # User exists ?
            if Q is None:
                 flash(f'User does not exists', 'danger')
            # Valid password ?
            elif not (Q and bcrypt.check_password_hash(Q.password, form.password.data)):
                flash(f'Invalid Login', 'danger')
            else:
                flash(f'Logged in successfully', 'success')
                session["users_id"] = Q.id
                session["email"] = Q.email
                session["username"] = Q.username
                session["password"] = Q.password
                session["logged_in"] = True

                if next_url:
                    return redirect(next_url)
                

        except Exception as e:
            flash(f'Connection Error {e}', 'warning')

        
        return redirect(url_for("home"))

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()
    session["logged_in"] = False

    # Redirect user to login index
    return redirect(url_for("home"))


@app.route("/details/<int:bookid>", methods=["GET","POST"])
@login_required
def details(bookid):
    if request.method == "GET":
        data = getData(bookid)
        if(not('comments' in data)):
            data['comments'] = []
        return render_template("details.html", result=data, comment_list=data['comments'] , bookid=bookid)
    else:
        ######## Check if the user commented on this particular book before ###########
        user_reviewed_before = db.execute("SELECT * from reviews WHERE users_id = :users_id AND books_id = :book_id",  {"users_id": session["users_id"], "book_id": bookid}).fetchone()
        if user_reviewed_before:
            flash(f'You reviewed this book before!', 'warning')
            return redirect(url_for("details", bookid=bookid))
        ######## Proceed to get user comment ###########
        user_comment = request.form.get("comments")
        user_rating = request.form.get("rating")

        if not user_comment:
            flash(f'Comment section cannot be empty!', 'danger')
            return redirect(url_for("details", bookid=bookid))

        # try to commit to database, raise error if any
        try:
            db.execute("INSERT INTO reviews (users_id, books_id, review_score, review_msg) VALUES (:users_id, :books_id, :review_score, :review_msg)",
                           {"users_id": session["users_id"], "books_id": bookid, "review_score":user_rating, "review_msg": user_comment})
        except Exception as e:
            flash(f'Error occured', 'warning')

        #success - redirect to details page
        db.commit()
        return redirect(url_for("details", bookid=bookid))


@app.route("/api/<isbn>")
@login_required
def api(isbn):
    data = getData(0,isbn)
    if(data == {}):
        data = {
            "error": "True",
            "message": "ISBN not found"
        }
    return jsonify(data)
    
@app.route("/del_review/<int:bookid>/<int:review_id>")
@login_required
def del_review(bookid, review_id):
    db.execute("DELETE from reviews WHERE id = :id", {"id": review_id})
    db.commit()
    return redirect(url_for("details", bookid=bookid))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404