from hashlib import pbkdf2_hmac, sha256
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from functools import wraps
from datetime import date
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') 
Bootstrap(app)


uri = os.environ.get('DATABASE_URL')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(uri,'sqlite:///user.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


        # Login Form:
class LoginForm(FlaskForm):
    name = StringField('Your Name:', validators=[DataRequired()])
    password = PasswordField('Enter your password:', validators=[DataRequired()])
    login = SubmitField('Login')



#SQL DB user object:
class User(UserMixin, db.Model):
    # __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True) # unique is causing the db issue:
    password = db.Column(db.String(150))

    # SQL Relationship with Notes(Parent):
    notes = db.relationship('Note', back_populates='user')

    def __repr__(self):
        return f"User class ref: {self.id}, {self.name}, {self.password}>"


#SQL DB Post object:
class Note(db.Model):
    # __tablename__ = 'user_notes'
    id = db.Column(db.Integer, primary_key=True)
    
    # SQL Relationship with User (Child):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", back_populates='notes')

    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)

# db.create_all()

# Create User and tester accts and hashing:
master_password = 'testtesttest'
master_password_hashed_salted = generate_password_hash(master_password, method='pbkdf2:sha256', salt_length=8)
# print(master_password_hashed_salted)

tester_password = 'testtest'
tester_password_hashed_salted = generate_password_hash(tester_password, method='pbkdf2:sha256', salt_length=8)
# print(tester_password_hashed_salted)

# m_t_password = 'testtesttest'
# t_t_password = 'testtest'
# password_decode = check_password_hash(master_password_hashed_salted, password)

# first_user = User(name='chayne', password=master_password_hashed_salted)
# test_user = User(name='test', password=tester_password_hashed_salted)

# db.session.add(first_user)
# db.session.add(test_user)

# NOTES INSERT DB:
 
# tester_string = 'this is a test note for "test" profile.'
# admin_string = 'this is a test note for "admin" profile.'
# test_note = Note(text=tester_string, date=date.today().strftime("%B %d, %Y"))
# admin_note = Note(text=admin_string, date=date.today().strftime("%B %d, %Y"))

# db.session.add(test_note)
# db.session.add(admin_note)

# db.session.commit()



''' Add flask_login initializer and info:
    Flask_login Module assignment:
    Step 1 for Authorization: (See STEP 0 @ 'User' Class). '''
login_manager = LoginManager()
login_manager.init_app(app)


''' Add flask_login initializer and info:
    FINAL STEP for Authorization groundwork before user registration: (See STEP 2 @ 'load_user(user_id)')
    Decorator wrap created for ADMIN:  
    funct to tie login status to 'admin' user, HIGHER ACCESS TO WEBSITE.
    - https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/#login-required-decorator'''
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # print(f"admin funct: ", *args, **kwargs)

        if current_user.id != 1 or current_user.id != 2:
            return abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

''' Add flask_login initializer and info:
    Step 2 for Authorization: (See STEP 1 @ 'login_manager')
    Used for simple users, all with same credentials: '''
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    print(f"in @load_user() -> tapping into db to search for user:\nuser id: {user.id}, user: {user.name}")
    return user


img_bank = (os.listdir('./static/img'))

# with open('static/img') as img_bank:
#     print(img_bank)

@app.route('/', methods=['GET', 'POST'])
def home():
    
    print(current_user)

    img_rand_choice = random.choice(img_bank)
    print(img_rand_choice)


    # DB check for what's in the DB:
    users_listed = db.session.query(User).all()
    print(users_listed)

    if request.method == 'POST':
        note_text = request.form.get('note')
        print(note_text)

        new_note = Note(text=note_text, date=date.today().strftime("%B %d, %Y"), user_id=current_user.id)
        # print(note.date)
        db.session.add(new_note)
        db.session.commit()
        # print(note.current_user)

    return render_template('index.html', user=current_user, img=f'static/img/{img_rand_choice}')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        name = request.form.get('name')
        password = request.form.get('password')
        print(f"name: {name}, password:{password}")

        user = User.query.filter_by(name=name).first()

        if not user:
            print('user not registered.')
            flash("That user doesn't exist")
            return redirect(url_for('login'))
        
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        
        else:
            login_user(user)
            return redirect(url_for('home', user=current_user))

    
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/delete/<int:note_id>')
@login_required
def delete_note(note_id):
    print(note_id)
    note_to_delete = Note.query.get(note_id)
    db.session.delete(note_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4999)
    # app.run(debug=True)