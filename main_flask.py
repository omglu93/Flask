from datetime import datetime, timedelta
# from enum import unique
# from hashlib import sha256
from flask import Flask, request
from flask_restful import Api, Resource, reqparse, inputs
from sqlalchemy.sql.elements import and_
from functools import wraps
import re
from data_requester import GetWeatherDDData
from database import *
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import uuid
from db import db

app = Flask(__name__)

app.config["SECRET_KEY"] = "somekey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///degree_data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
api = Api(app)

#### JSON Arguments ####

input_args = reqparse.RequestParser()
input_args.add_argument("consumption", type=float, required=False)
input_args.add_argument("start_date", type=datetime, required=True)
input_args.add_argument("end_date", type=datetime, required=True)

create_user_args = reqparse.RequestParser()
create_user_args.add_argument("e_mail", type=str)
create_user_args.add_argument("password", type=str)

request_dd_args = reqparse.RequestParser()
request_dd_args.add_argument("location", type=str)
request_dd_args.add_argument("date_one", type=str)
request_dd_args.add_argument("date_two", type=str)


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

class DDRequest(Resource):

    def __init__(self):
        args = request_dd_args.parse_args()
        self.location = args["location"]
        self.date_one = args["date_one"] #datetime.strptime(args["date_one"], "%d-%m-%Y %H:%M")
        self.date_two = args["date_two"]

    def get(self):
        """TODO 
        1. Create a link to the database, so that the get request checks
        if the data is available in the database before it sends out the request
        if no the data should be requested and the database updated with it.
        """
        ### Add and for date_two as a range, filter for location
        sql_query = f"SELECT * FROM degree_data_table WHERE '{self.date_one}' > datetime "\
                    f"AND '{self.date_two}' < datetime AND location_id = "\
                    f"(SELECT id FROM location_table WHERE location == '{self.location}')" 

        ### Normal query() type calls have some issues with sqlite and datetime in this version
        
        historic_data = db.session.execute(sql_query).fetchall()

        if bool(historic_data):
            print(historic_data)
        else:
            print("empty")
                             
        #current_user = UserTable.query.filter_by(public_id = data["public_id"]).first()
        # if bool(historic_data):
        #     data = historic_data
        # else:
            #data = GetWeatherDDData(location=self.location,
            #                        time_period=self.date_one).generate_dd()
        print(historic_data)
        #json_file = historic_data.to_json(orient="index")

        #return json_file, 201
        


api.add_resource(CreateUser, "/create-user")
api.add_resource(UserLogin, "/login")
api.add_resource(DDRequest, "/degree_data")

if __name__ == "__main__":
    app.run(debug=True)
    #db.create_all()
    # admin = UserTable(public_id="admin", e_mail="admin@example.com", password="12345678", admin= 1)
    # location = LocationTable(location = "London")
    # db.session.add(location)
    # db.session.commit()