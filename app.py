import os
from datetime import datetime,date
from flask import Flask, redirect, render_template, session, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import speech_recognition as sr

app = Flask(__name__)
app.secret_key = "secret key"

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_AUDIO = {'wav'}

# creating or importing the databases
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DataBase.db'    # this is a relative path to the database

# linking the databases to the server
db = SQLAlchemy(app)


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100),nullable=False)
    last_name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),nullable=False,unique=True)
    password = db.Column(db.String(100),nullable=False)
    image_name = db.Column(db.String(100))
    
    def __repr__(self):
        return "<user %r>" % self.id
    
class course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    description = db.Column(db.String(1000),nullable=False)
    image_name = db.Column(db.String(100),nullable=False)
    
    def __repr__(self):
        return "<Course %r>" % self.id
    
@app.route("/",methods=["GET"])
def index():
    courses = course.query.all()
    rows_json = [{'id': row.id, 'title': row.title, 'description': row.description, 'image_name': row.image_name, } for row in courses]
    return jsonify(rows_json)
    
@app.route('/register',methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        f_name = data.get('first_name')
        l_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        
        new_user = user(first_name=f_name,last_name=l_name,email=email,password=password)
        
        if user.query.filter_by(email=email).first():
            return jsonify({'error': 'Username already exists'}), 400
        else:
            
            db.session.add(new_user)
    
            try:
                db.session.commit()
                session['id'] = new_user.id
                session['email'] = new_user.email
                session['first_name'] = new_user.first_name
                session['last_name'] = new_user.last_name
                return jsonify({'message': 'Signup successful',
                                'first_name':new_user.first_name,
                                'last_name':new_user.last_name,
                                'email':new_user.email,}), 201
            except:
                db.session.rollback()
                return jsonify({'error': 'An error occurred during signup'}), 500
            
    
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        
        if user_:=user.query.filter_by(email=email).first():
            if user_.password == password:
                session['id'] = user_.id
                session['email'] = user_.email
                session['first_name'] = user_.first_name
                session['last_name'] = user_.last_name
                return jsonify({'message': 'Loggin in successful',
                                'first_name':user_.first_name,
                                'last_name':user_.last_name,
                                'email':user_.email,}), 201
            else:
                return jsonify({'error': 'Password wrong'}), 400
        else:
            return jsonify({'error': 'Email address doesnt exist'}), 404
    
@app.route('/logout')
def logout():
    session.clear()
    return url_for('login')    

@app.route('/add_profile_image',methods=['POST','GET'])
def add_profile_image():
    if session.get("email"):
        if request.method == 'POST':
            if 'image' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file and allowed_file(file.filename):
                filename = str(user.query.filter_by(email=session.get("email")).first().id) +".png"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                user.query.filter_by(email=session.get("email")).first().image_name = filename
                db.session.commit()
                return jsonify({'message': 'Image uploaded successfully'}), 200
            else:
                return jsonify({'error': 'Invalid file type'}), 400
    else:
        return url_for("login")
    
@app.route('/add_image',methods=['POST','GET'])
def add_image():
    if session.get("email"):
        if request.method == 'POST':
            if 'image' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file and allowed_file(file.filename,0):
                filename = str(user.query.filter_by(email=session.get("email")).first().id) +".png"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                user.query.filter_by(email=session.get("email")).first().image_name = filename
                db.session.commit()
                return jsonify({'message': 'Image uploaded successfully'}), 200
            else:
                return jsonify({'error': 'Invalid file type'}), 400
        else:
            return url_for("index")
    else:
        return url_for("login")

@app.route('/audio',methods=['POST','GET'])
def audio():
    recognizer = sr.Recognizer()
    if session.get("email"):
        if request.method == 'POST':
            if 'audio' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['audio']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file and allowed_file(file.filename,1):
                with sr.AudioFile(file) as source:
                    audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    return jsonify({'message': 'Audio transcribed successfully', 'text':text}), 200
                except sr.UnknownValueError:
                    return jsonify({'error': 'Audio couldnt be transcribed'}), 400
                except sr.RequestError as e:
                    return jsonify({'message': 'Couldnt get a result'}), 400
                
                
            else:
                return jsonify({'error': 'Invalid file type'}), 400
        else:
            return url_for("index")
    else:
        return url_for("login")
def allowed_file(filename,type):
    if type == 0:
        return '.' in  filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGE
    else:
        return '.' in  filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_AUDIO
        
        
if __name__ == '__main__':
    if not os.path.exists("instance\DataBase.db"):
        with app.app_context():
            db.create_all()
            print("created database")
    app.run(debug=True)