from crypt import methods
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'movies.db')
app.config['JWT_SECRET_KEY'] = 'my-super-secret-key'  # change this in real life
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']


# Initialize db
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command("db_create")
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.route('/')
def hello_world():
    return jsonify(message='Hello from the movie api!')


# Retrive all movies from db table
@app.route('/movies', methods=["GET"])
def get_movies():
    all_movies = Movie.query.all()
    result = movies_schema.dump(all_movies)
    return jsonify(result.data)


@app.route('/movie_details/<int:movie_id>', methods=['GET'])
def movie_details(movie_id: int):
    movie = Movie.query.filter_by(movie_id=movie_id).one_or_none()
    if movie:
        result = movie_schema.dump(movie)
        return jsonify(result.data)
    else:
        return jsonify(message='Movie not found for given id!'), 404    


@app.route('/register', methods=["POST"])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).one_or_none()

    if test:
        return jsonify(message="The user already registered!"), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name'] 
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="New user registered!"), 201 


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password'] 
    else:    
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).one_or_none()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Successful login!', access_token=access_token)
    else:
        return jsonify(message='Bad email or password'), 401


@app.route('/retrieve_email/<string:email>', methods=['GET'])
def retrieve_email(email: str):
    print(email)
    user = User.query.filter_by(email=email).one_or_none()
    if user:
        msg = Message("Your password is " + user.password,
                      sender="admin@movieapi.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(Message='Your password is sent to '+email)
    else:
        return jsonify(message='The email is not found '+email), 401


@app.route('/add_movie', methods=['POST'])
@jwt_required
def add_movie():
    movie_name = request.form['movie_name']
    movie = Movie.query.filter_by(movie_name=movie_name).one_or_none()
    if movie:
        return jsonify(message='The movie already added!'), 409
    else:
        director = request.form['director']
        writer = request.form['writer']
        stars = request.form['stars']
        IMDB_rating = request.form['IMDB_rating']
        new_movie = Movie(movie_name=movie_name, director=director, writer=writer, stars=stars, IMDB_rating=IMDB_rating)
        db.session.add(new_movie)
        db.session.commit()
        return jsonify(message='You added the movie! ' + movie_name), 201


@app.route('/update_movie/<int:movie_id>', methods=['PUT'])
@jwt_required
def update_movie(movie_id: int):
    movie = Movie.query.filter_by(movie_id=movie_id).one_or_none()
    if movie:
        movie.movie_name = request.form['movie_name']
        movie.director = request.form['director']
        movie.writer = request.form['writer']
        movie.stars = request.form['stars']
        movie.IMDB_rating = request.form['IMDB_rating']
        db.session.commit()
        return jsonify(message='You update the movie!'), 202
    else:
        return jsonify(message='The movie does not exist!'), 404   


@app.route('/delete_movie/<int:movie_id>', methods=['DELETE'])
@jwt_required
def delete_movie(movie_id: int):
    movie = Movie.query.filter_by(movie_id=movie_id).one_or_none()
    if movie:
        db.session.delete(movie)
        db.session.commit()
        return jsonify(message='The movie deleted!'), 202
    else:
        return jsonify(message='The movie does not exist!'), 404


# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Movie(db.Model):
    __tablename__ = 'movies'
    movie_id = Column(Integer, primary_key=True, unique=True)
    movie_name = Column(String)
    director = Column(String)
    writer = Column(String)
    stars = Column(String)
    IMDB_rating = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class MovieSchema(ma.Schema):
    class Meta:
        fields = ('movie_id', 'movie_name', 'director', 'writer', 'stars', 'IMDB_rating')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)


if __name__ == '__main__':
    app.run(debug=True)
