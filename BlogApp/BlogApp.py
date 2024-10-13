from flask import Flask, render_template, request, redirect, url_for, flash
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
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        mongo.db.posts.insert_one({'title': title, 'content': content})
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': {'title': title, 'content': content}})
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('edit.html', post=post)

@app.route('/delete/<post_id>')
def delete_post(post_id):
    mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
    mongo.db.comments.delete_many({'post_id': post_id})  # Optionally delete associated comments
    return redirect(url_for('home'))

@app.route('/comment/<post_id>', methods=['POST'])
def comment(post_id):
    content = request.form['content']
    mongo.db.comments.insert_one({'post_id': post_id, 'content': content})
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Fetch user from the database using the provided username
        user = mongo.db.users.find_one({'username': request.form['username']})

        # If the user exists, check the password
        if user:
            # Verify if the provided password matches the stored hashed password
            if check_password_hash(user['password'], request.form['password']):
                # If password is correct, return a welcome message
                return f"Welcome, {user['username']}"
            else:
                # If password is incorrect, call LoginFailed()
                return LoginFailed()
        else:
            # If the user is not found, call LoginFailed()
            return LoginFailed()

    # If request method is GET, render the login page
    return render_template('login.html')

# Function to handle login failures
def LoginFailed():
    # Flash an error message to the user
    flash("Please check your username or password.", "danger")
    # Redirect the user back to the login page
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('signup.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
