from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os as os

app = Flask(__name__)

app.secret_key = os.getenv('SECRET')

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGODBPATH")
mongo = PyMongo(app)

@app.route('/')
def home():
    posts = mongo.db.posts.find()
    return render_template('home.html', posts=posts)

@app.route('/post/<post_id>')
def view_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    comments = mongo.db.comments.find({'post_id': post_id})
    return render_template('post.html', post=post, comments=comments)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    # Check if user is logged in
    if 'username' not in session:
        flash('You need to be logged in to create a post.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # Include the username in the post document
        mongo.db.posts.insert_one({
            'title': title,
            'content': content,
            'username': session['username']
        })
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    # Check if the logged-in user is the owner of the post
    if 'username' not in session or session['username'] != post['username']:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        mongo.db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'title': title, 'content': content}}
        )
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('edit.html', post=post)

@app.route('/delete/<post_id>')
def delete_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if session['username'] != post['username']:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))
    mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
    mongo.db.comments.delete_many({'post_id': post_id})  # delete associated comments
    return redirect(url_for('home'))

@app.route('/comment/<post_id>', methods=['POST'])
def comment(post_id):
    # Check if user is logged in
    if 'username' not in session:
        flash('You need to be logged in to comment.', 'danger')
        return redirect(url_for('login'))
    content = request.form['content']
    mongo.db.comments.insert_one({
        'post_id': post_id,
        'content': content,
        'username': session['username']
    })
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'username': request.form['username']})
        if user:
            if check_password_hash(user['password'], request.form['password']):
                # Set the username in session
                session['username'] = user['username']
                flash(f"Welcome, {user['username']}!", "success")
                return redirect(url_for('home'))
            else:
                return LoginFailed()
        else:
            return LoginFailed()
    return render_template('login.html')

# Function to handle login failures
def LoginFailed():
    # Flash an error message to the user
    flash("Please check your username or password.", "danger")
    # Redirect the user back to the login page
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Check if the username already exists
        if mongo.db.users.find_one({'username': username}):
            flash("Username already exists.", "danger")
            return redirect(url_for('signup'))

        # Insert the new user into the database
        mongo.db.users.insert_one({'username': username, 'password': hashed_password})
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
