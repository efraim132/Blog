from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import os as os

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
