from datetime import datetime, timedelta
from enum import unique
from hashlib import sha256
from flask import Flask, request
from flask_restful import Api, Resource, reqparse, inputs
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import re

from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import uuid


app = Flask(__name__)

app.config["SECRET_KEY"] = "somekey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///degree_data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.init_app(app)

#### Database Classes ####

class LocationTable(db.Model):

    __tablename__ = "location_table"
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Primary key: {self.id} ---- Location: {self.location}"

class DegreeDataTable(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_table.id"), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, unique=False)
    temp_c = db.Column(db.Float, nullable=False, unique=False)
    CDD_10_5 = db.Column(db.Float, nullable=False, unique=False)
    CDD_15_5 = db.Column(db.Float, nullable=False, unique=False)
    CDD_18_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_10_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_15_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_18_5 = db.Column(db.Float, nullable=False, unique=False)

    def __repr__(self) -> str:
        return f"Degree key: {self.degree_key} /n base_temperature: {self.temp_c}"

class UserTable(db.Model):

    user_id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    e_mail = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean, unique=False)

    def __repr__(self) -> str:
        return f"e_mail: {self.e_mail} /n admin: {self.admin}"

api = Api(app)

#### JSON Arguments ####

input_args = reqparse.RequestParser()
input_args.add_argument("consumption", type=float, required=False)
input_args.add_argument("start_date", type=datetime, required=True)
input_args.add_argument("end_date", type=datetime, required=True)

create_user_args = reqparse.RequestParser()
create_user_args.add_argument("e_mail", type=str)
create_user_args.add_argument("password", type=str)


#### Token Generator ####

def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        token = None

        if "x-acess-token" in request.headers:
            token = request.headers["x-acess-token"]
        if not token:
            return {"message" : "Token is missing"}
        
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
            current_user = UserTable.query.filter_by(public_id = data["public_id"]).first()
        except:
            return {"message" : "Token is invalid"}
        return function(current_user, *args, **kwargs)
    return decorated


class CreateUser(Resource):

    REGEX_E_MAIL_VALIDATION = re.compile(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+")

    def __init__(self):
        args = create_user_args.parse_args()
        self.e_mail = self._email_validator(args["e_mail"])
        self.password = generate_password_hash(args["password"], method="pbkdf2:sha256")
        self.public_id = str(uuid.uuid4())
        self.admin = False

    def get(self):
        print(self.e_mail)
        return {"user" : self.e_mail}, 201

    def post(self):

        if len(self.password) < 6:
            return {"error" : "Password is too short!"}

        new_user = UserTable(public_id=self.public_id,
                             e_mail = self.e_mail,
                             password = self.password,
                             admin = self.admin
                            )
        db.session.add(new_user)
        db.session.commit()

        return {"message" : "New user created!"}

    ## Future changes: move to seperate modul
    def _email_validator(self, email): 
        if re.fullmatch(self.REGEX_E_MAIL_VALIDATION, email):
            return email
        else:
            return {"error" : "E-mail is not valid!"}

class UserLogin(Resource):

    def __init__(self):
        self.auth = request.authorization

    def get(self):

        if not self.auth or not self.auth.username or not self.auth.password:
            return {"message" : "Could not verify!"}

        user = UserTable.query.filter_by(e_mail=self.auth.username).first()
        if not user:
            return {"message" : "Could not verify!"}


        if check_password_hash(user.password, self.auth.password):
            token = jwt.encode({"public_id" : user.public_id,
                                "exp" : datetime.utcnow() + timedelta(minutes=90) 
                                }, app.config["SECRET_KEY"])
            return {"token" : token}

        return {"message" : "Could not verify!"}

api.add_resource(CreateUser, "/create-user")
api.add_resource(UserLogin, "/login")

# if __name__ == "__main__":
    #app.run(debug=True)
    #db.create_all()
    # admin = UserTable(public_id="admin", e_mail="admin@example.com", password="12345678", admin= 1)
    # location = LocationTable(location = "London")
    # db.session.add(location)
    # db.session.commit()