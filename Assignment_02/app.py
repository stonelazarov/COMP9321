import json
import jwt
import datetime

from time import time
from itsdangerous import SignatureExpired

from flask_restplus import Resource, Api, abort
from flask_restplus import reqparse
from flask_restplus import fields

from functools import wraps
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_

from Data import content_based as data
from Data import user_item_knn as knn

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'justasecretkey'

api = Api(app, authorizations={
    'API-KEY': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'AUTH-TOKEN'
    }
},
          security='API-KEY',
          default="movies",  # Default namespace
          title="Monks movies theater",  # Documentation Title
          description="This is a demo of the assignment.")  # Documentation Description

db = SQLAlchemy(app)


class AuthenticationToken:
    def __init__(self, secret_key, expires_in):
        self.secret_key = secret_key
        self.expires_in = expires_in

    def generate_token(self, username):
        info = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.expires_in)
        }
        token = jwt.encode(info, self.secret_key, algorithm='HS256')
        print(token)
        return token.decode('ASCII')

    def validate_token(self, token):

        info = jwt.decode(token, self.secret_key, algorithms=['HS256'])

        current_time = time()
        if query_user(info['username']) and current_time < info['exp']:
            return info
        else:
            raise SignatureExpired


SECRET_KEY = "A SECRET KEY; USUALLY A VERY LONG RANDOM STRING"
expires_in = 600
auth = AuthenticationToken(SECRET_KEY, expires_in)


def record_api(api_name):
    record = APIRecord(api_name=api_name, access_time=time())
    db.session.add(record)
    db.session.commit()


user_auth = api.namespace('auth', description='User Authentication Services')
user_account = api.namespace('account', description='User Information Services')
api_analytics = api.namespace('analytics', description='API Analytics for Admin')

login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str)
login_parser.add_argument('password', type=str)


@user_auth.route('/login', strict_slashes=False)
class Login(Resource):
    @user_auth.response(200, 'Success')
    @user_auth.response(403, 'Invalid Username/Password')
    @user_auth.expect(login_parser, validate=True)
    @user_auth.doc(description='''
        Use this endpoint to login, username and password must be matched in the database.
        Once login successfully, return a token could be used for 10 minutes for user.
    ''')
    def get(self):
        record_api('login')
        args = login_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        user = valid_login(username, password)
        if user:
            session['uid'] = user.uid
            session['username'] = username
            return {"token": "" + auth.generate_token(username), "uid": user.uid}
        else:
            abort(403, 'Invalid Username/Password')


@user_auth.route('/logout', strict_slashes=False)
class Logout(Resource):
    @user_auth.response(200, 'Success')
    @user_auth.response(403, 'Unknown Error')
    @user_auth.doc(description='Use this endpoint to logout')
    def put(self):
        record_api('logout')
        session.pop('username', None)
        session.pop('uid', None)


register_parser = reqparse.RequestParser()
register_parser.add_argument('email', type=str)
register_parser.add_argument('username', type=str)
register_parser.add_argument('password1', type=str)
register_parser.add_argument('password2', type=str)


@user_auth.route('/register', strict_slashes=False)
class Register(Resource):
    @user_auth.response(200, 'Success')
    @user_auth.response(403, 'Invalid Username/Password')
    @user_auth.expect(register_parser, validate=True)
    @user_auth.doc(description='''
        Use this endpoint to register, username and password must be matched in the database.
        Once login successfully, return a token could be used for 10 minutes for user.
    ''')
    def post(self):
        record_api('register')
        args = login_parser.parse_args()
        email = args.get('email')
        username = args.get('username')
        password1 = args.get('password1')
        password2 = args.get('password2')

        if password1 != password2:
            return {"message": "Two passwords should be the same."}, 403
        elif not valid_regist(username, email):
            return {"message": "This account has been registered, please login."}, 403
        else:
            # fatal: uid is set as 350 as default, this is because the dataset is borrowed
            # we cannot synchronize the local info with the Netflix database, so we randomly
            # pick one here as default value of uid
            user = User(username=username,
                        password=password1,
                        email=email,
                        uid=350)
            db.session.add(user)
            db.session.commit()
            session['uid'] = user.uid
            session['username'] = username
            return {"token": "" + auth.generate_token(username), "uid": user.uid}


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers.get('AUTH-TOKEN')
        if not token:
            abort(401, 'Authentication token is missing')
        try:
            user_info = auth.validate_token(token)

        except Exception as e:
            abort(401, str(e))

        return f(*args, **kwargs)

    return decorated


@api_analytics.route('/analytics', strict_slashes=False)
class APIAnalytics(Resource):
    @user_auth.response(200, 'Success')
    @user_auth.response(403, 'Unknown Error')
    @user_auth.doc(description='Use this endpoint to View the usage of APIs')
    @requires_auth
    def get(self):
        return query_api_usage()


# The following is the schema of Movie
movie_model = api.model('Movie', {
    'title': fields.String,
    'id': fields.Integer,
    'genres': fields.String,
    'homepage': fields.String,
    'overview': fields.String,
    'poster_path': fields.String,
    'production_companies': fields.String,
    'popularity': fields.Integer
})


@api.route('/movies/<int:id>')
@api.param('id', 'The Movie identifier')
class Movies(Resource):
    @api.response(404, 'Movie was not found')
    @api.response(200, 'Successful')
    @api.doc(description="Get a movie by its ID")
    @requires_auth
    def get(self, id):
        record_api('movie_by_id')
        df = knn.detail_by_id(id)
        if df.empty:
            api.abort(404, "Movie {} doesn't exist".format(id))

        json_str = df.to_json(orient='index')
        ds = json.loads(json_str)

        ret = []

        for idx in ds:
            movie = ds[idx]
            movie['id'] = int(movie['id'])
            ret.append(movie)

        return ret


recommend_parser = reqparse.RequestParser()
recommend_parser.add_argument('user_id', type=int)


@api.route('/movies/recommend')
class RecommendMovies(Resource):

    @requires_auth
    @api.response(200, 'Successful')
    @api.doc(description="Get recommend movies")
    @api.expect(recommend_parser, validate=True)
    def get(self):
        record_api('recommend')
        args = recommend_parser.parse_args()
        user_id = args.get('user_id')

        df = knn.recommend_user(user_id)
        print(df)
        json_str = df.to_json(orient='index')
        # convert the string JSON to a real JSON
        ds = json.loads(json_str)
        ret = []

        for idx in ds:
            movie = ds[idx]
            detail_link = "http://127.0.0.1:5000/movies/" + str(movie['movie_id'])
            movie['detail_link'] = detail_link
            ret.append(movie)

        return ret


similar_parser = reqparse.RequestParser()
similar_parser.add_argument('movie_name', type=str)


@api.route('/movies/similar')
class SimilarMovies(Resource):

    @requires_auth
    @api.response(200, 'Successful')
    @api.doc(description="Get recommend movies")
    @api.expect(similar_parser, validate=True)
    def get(self):
        record_api('similar')
        args = similar_parser.parse_args()
        movie_name = args.get('movie_name')

        df = data.find_similar_movie(movie_name)
        print(df)
        json_str = df.to_json(orient='index')
        # convert the string JSON to a real JSON
        ds = json.loads(json_str)
        ret = []

        for idx in ds:
            movie = ds[idx]
            movie['id'] = int(movie['id'])
            detail_link = "http://127.0.0.1:5000/movies/" + str(movie['id'])
            movie['detail_link'] = detail_link
            ret.append(movie)

        return ret


@api.route('/movies/popular')
class PopularMovies(Resource):

    @requires_auth
    @api.response(200, 'Successful')
    @api.doc(description="Get top10 popular movies")
    def get(self):
        record_api('popular')
        df = knn.popular_movies()
        print(df)
        json_str = df.to_json(orient='index')
        # convert the string JSON to a real JSON
        ds = json.loads(json_str)
        ret = []

        for idx in ds:
            movie = ds[idx]
            movie['id'] = int(movie['id'])
            detail_link = "http://127.0.0.1:5000/movies/" + str(movie['id'])
            movie['detail_link'] = detail_link
            ret.append(movie)

        return ret


@user_account.route('/<int:id>', strict_slashes=False)
@api.param('id', 'The User id')
class Accounts(Resource):

    def get(self, id):
        record_api('user_by_id')

        uid_ = int(session['uid'])
        # This restriction is not necessary actually
        # if uid_ != id:
        #     return {'message': 'Illegal request'}, 403

        user = User.query.filter(User.uid == str(id)).first()
        if user:
            return {'username': user.username, 'uid': user.uid, 'email': user.email}
        else:
            return {'message': 'User not exists'}


############################################
# database
############################################

# ORM
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    uid = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


class APIRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_name = db.Column(db.String(80))
    access_time = db.Column(db.String(80))

    def __repr__(self):
        return '<APIRecord %r>' % self.api_name


# db creation
@app.before_first_request
def create_db():
    db.drop_all()  # drop and create for each time launch, could be better
    db.create_all()

    admin = User(username='admin', password='root', uid="256", email='admin@example.com')
    db.session.add(admin)

    guestes = [User(username='guest1', password='guest1', uid="257", email='guest1@example.com'),
               User(username='guest2', password='guest2', uid="258", email='guest2@example.com'),
               User(username='guest3', password='guest3', uid="259", email='guest3@example.com'),
               User(username='guest4', password='guest4', uid="260", email='guest4@example.com')]
    db.session.add_all(guestes)
    db.session.commit()


# caching
@app.after_request
def add_header(response):
    # response.cache_control.max_age = 300
    return response


############################################
# db helper and decorator
############################################


# validation of login
def valid_login(username, password):
    user = User.query.filter(and_(User.username == username, User.password == password)).first()
    return user


# validation of register
def valid_regist(username, email):
    user = User.query.filter(or_(User.username == username, User.email == email)).first()
    if user:
        return False
    else:
        return True


def query_user(username):
    user = User.query.filter(or_(User.username == username)).first()
    if user:
        return True
    else:
        return False

def query_api_usage():
    currentTime = time()
    one_day = 60 * 60 * 24
    all_records = len(APIRecord.query.filter(or_(True)).all())
    login = len(APIRecord.query.filter(and_((APIRecord.api_name == 'login'),(currentTime - APIRecord.access_time <= one_day))).all())
    logout = len(APIRecord.query.filter(and_((APIRecord.api_name == 'logout'),(currentTime - APIRecord.access_time <= one_day))).all())
    register = len(APIRecord.query.filter(and_((APIRecord.api_name == 'register'),(currentTime - APIRecord.access_time <= one_day))).all())
    movie_by_id = len(APIRecord.query.filter(and_((APIRecord.api_name == 'movie_by_id'),(currentTime - APIRecord.access_time <= one_day))).all())
    recommend = len(APIRecord.query.filter(and_((APIRecord.api_name == 'recommend'),(currentTime - APIRecord.access_time <= one_day))).all())
    similar = len(APIRecord.query.filter(and_((APIRecord.api_name == 'similar'),(currentTime - APIRecord.access_time <= one_day))).all())
    popular = len(APIRecord.query.filter(and_((APIRecord.api_name == 'popular'),(currentTime - APIRecord.access_time <= one_day))).all())
    user_by_id = len(APIRecord.query.filter(and_((APIRecord.api_name == 'user_by_id'),(currentTime - APIRecord.access_time <= one_day))).all())
    return {'all_records':all_records,
            'login':login,
            'logout':logout,
            'register':register,
            'movie_by_id': movie_by_id,
            'recommend': recommend,
            'similar': similar,
            'popular':popular ,
            'user_by_id':user_by_id
            }


if __name__ == '__main__':
    app.run(debug=True)
