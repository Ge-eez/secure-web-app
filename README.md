This is a Flask based project using Postgresql as Database technology.

In the home page it renders 10 random books. And a user can see the details of a book by either clicking on the arrow link or by searching in the search bar (this operation can be done by using ISBN, Title, or Author).

A user must sign in first to access the details of a book, or search for a book.

In templates folder, there are structure templates of the HTML files to be rendered
In static folder , there are static files (images, css, js, and fontawesome designs)
In books.csv file, there are  the books contained in this application
In formy.py file, there are login form structure and register form structure created
In application.py, there are all the functionalities of the app, including the routes, and their functions.
In import.py, there are the functions we first need to run when we change our Database url.
In Procfile is the Heroku code to be run when Heroku builds the app
In links.md is the link of the hosted Heroku app.
In wsgi.py is the command to be executed when the app runs
In requirements.txt, there are lists of packages and dependencies required for the application.

This webapp redirects to 404 page not found page when requested to get unknown url
