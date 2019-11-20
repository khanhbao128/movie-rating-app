"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template('homepage.html')


@app.route('/register')
def register_form():
    """Display a registration form to the users"""
    return render_template('register_form.html')

@app.route('/register', methods=['POST'])
def register_user():
    """Verify user's info"""
    email = request.form.get('email')
    password = request.form.get('password')
    age = request.form.get('age')
    zipcode = request.form.get('zipcode')

    # check user's email to see if that user already exists in the database
    user = User.query.filter_by(email=email).first()
    # if user exists, check to see if the password entered matches the database password
    if user:
        flash("This user already exists. Please login.")
        return redirect('/login')
    else:
        new_user = User(email=email, password=password, age=age, zipcode=zipcode)
        db.session.add(new_user)
        db.session.commit()
        flash(f"User {email} added.")
        return redirect('/')

@app.route('/login')
def login():
    """Show log in page"""

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def verify_user():
    """Verify if users info is correct and log them in"""

    #get info from users inputs
    email = request.form.get('email')
    password = request.form.get('password')

    #check to see if user exists
    user = User.query.filter_by(email=email).first()

    if user:
        #check if password matches database
        if password == user.password:
            session['user_id'] = user.user_id
            flash(f'{email} logged in')
            return redirect (f'/users/{user.user_id}')
        else:
            flash('Sorry the password is incorrect. Please enter the right password to login')
            return redirect('/login')
    else:
        flash("This user does not exists.")
        return redirect('/login')

@app.route('/logout')
def logout():
    """"Log out"""

    del session['user_id']
    flash("Logged Out")
    return redirect('/')

@app.route('/users')
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/users/<user_id>')
def show_user(user_id):
    """Show info of one particular user"""

    user = User.query.filter_by(user_id=user_id).first()
    return render_template('user.html', user=user)


@app.route('/movies')
def movie_list():
    """Show list of movies"""

    movies = Movie.query.order_by('title').all()
    return render_template('movie_list.html', movies=movies)      

@app.route('/movies/<movie_id>')
def show_movie(movie_id):
    """"Show info about movie

    If a user is logged in, let them add or edit a rating
    """

    movie = Movie.query.get(movie_id)

    user_id = session.get('user_id')

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    # return render_template('movie.html', 
    #                         movie=movie, 
    #                         user_rating=user_rating)   

    # Get average rating of movie

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it.

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    # Either use the prediction or their real rating

    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None


    return render_template('movie.html', 
                            movie=movie, 
                            user_rating=user_rating,
                            prediction=prediction)   



@app.route('/movies/<movie_id>', methods=['POST'])
def add_update_rating(movie_id):
    """Add or update a rating"""

    score = request.form.get('score')

    user_id = session.get('user_id')

    if not user_id:
        raise Exception('No user logged in.')

    rating = Rating.query.filter_by(user_id=user_id)
    
    if rating:
        rating.score = score
        flash("Rating updated.")
    else:
        rating = Rating(user_id=user_id, movie_id=movie_id, score=score)
        flash("Rating added.")
        db.session.add(rating)

    db.session.commit()

    return redirect(f'/movies/{movie_id}')




   


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
