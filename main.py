from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import math
from datetime import datetime
import os

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "super-secret-key"
# app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    # MAIL_USERNAME = params['gmail-user'],
    # MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(20), nullable=True)
    img_file = db.Column(db.String(20), nullable=True)


class Guest(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(20), nullable=True)
    img_file = db.Column(db.String(20), nullable=True)


class Admin(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.String(80), nullable=False)
    login = db.Column(db.String(20), nullable=True)


class Logout(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.String(80), nullable=False)
    logout = db.Column(db.String(20), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))

    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]

    if page == 1:
        prev = "#"
        next1 = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next1 = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next1 = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next1)


@app.route("/guesthome")
def guesthome():
    guests = Guest.query.filter_by().all()

    return render_template('guesthome.html', params=params, guests=guests)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients = [params['gmail-user']],
        #                   body = message + "\n" + phone
        #                   )
    return render_template('contact.html', params=params)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/guest", methods=['GET', 'POST'])
def guest_entries():
    # if 'user' in session and session['user'] == params['admin_user']:
    #     posts = Posts.query.all()
    #     return render_template('dashboard.html', params=params, posts=posts)
    if request.method == 'POST':
        box_title = request.form.get('title')
        tline = request.form.get('tline')
        slug = request.form.get('slug')
        content = request.form.get('content')
        img_file = request.form.get('img_file')
        guest = Guest(title=box_title, tagline=tline, slug=slug, content=content, img_file=img_file,
                      date=datetime.now())
        db.session.add(guest)
        db.session.commit()
    return render_template('guest.html', params=params)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        guests = Guest.query.all()
        return render_template('dashboard.html', params=params, posts=posts, guests=guests)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params["admin_user"] and userpass == params["admin_password"]:
            session['user'] = username
            admin = request.form.get('uname')
            entry_ad = Admin(admin=admin, login=datetime.now())
            db.session.add(entry_ad)
            db.session.commit()
            posts = Posts.query.all()
            guests = Guest.query.all()
            return render_template('dashboard.html', params=params, posts=posts, guests=guests)

    return render_template('login.html', params=params)


@app.route("/edit/<string:slno>", methods=['GET', 'POST'])
def edit(slno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if slno == '0':
                post = Posts(title=box_title, tagline=tline, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            #
            #
            else:
                post = Posts.query.filter_by(slno=slno).first()
                post.title = box_title
                post.slug = slug
                post.tagline = tline
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + slno)
        post = Posts.query.filter_by(slno=slno).first()

        return render_template('edit.html', params=params, post=post, slno=slno)


@app.route("/edits/<string:slno>", methods=['GET', 'POST'])
def edits(slno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            guest = Guest.query.filter_by(slno=slno).first()
            guest.title = box_title
            guest.slug = slug
            guest.tagline = tline
            guest.content = content
            guest.img_file = img_file
            guest.date = date
            db.session.commit()
            return redirect('/edits/' + slno)
        guest = Guest.query.filter_by(slno=slno).first()
        return render_template('guestedit.html', params=params, slno=slno, guest=guest)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)


@app.route("/guestpost/<string:post_slugs>", methods=['GET'])
def post_route_guest(post_slugs):
    guest = Guest.query.filter_by(slug=post_slugs).first()

    return render_template('guestposts.html', params=params, guest=guest)


# @app.route("/postg/<string:guest_slug>", methods=['GET'])
# def guest_post_route(guest_slug):
#     guest = Guest.query.filter_by(slug=guest_slug).first()
#
#     return render_template('guestposts.html', params=params, guest=guest)


#
@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded successfully"


@app.route("/logout")
def logout():
    entry_out = Logout(admin="admin", logout=datetime.now())
    db.session.add(entry_out)
    db.session.commit()
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:slno>", methods=['GET', 'POST'])
def delete(slno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(slno=slno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


@app.route("/guestdelete/<string:slno>", methods=['GET', 'POST'])
def guest_delete(slno):
    if 'user' in session and session['user'] == params['admin_user']:
        guest = Guest.query.filter_by(slno=slno).first()
        db.session.delete(guest)
        db.session.commit()
        return redirect('/dashboard')


app.run(debug=True)
