from datetime import date, datetime, timedelta
import logging
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from functools import wraps
import re
from data_requester import GetWeatherDDData, UpdateDB
from old.database import *
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import uuid
from db import db
import pandas as pd

#### Logger configuration ####
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(r"log\flask_rest.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formater)

#### Flask and DB configuration ####
app = Flask(__name__)

app.config["SECRET_KEY"] = "somekey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///degree_data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
api = Api(app)

#### JSON Arguments ####
create_user_args = reqparse.RequestParser()
create_user_args.add_argument("e_mail", type=str, required=True)
create_user_args.add_argument("password", type=str, required=True)

request_dd_args = reqparse.RequestParser()
request_dd_args.add_argument("location", type=str, required=True)
request_dd_args.add_argument("date_one", type=str, required=True)
request_dd_args.add_argument("date_two", type=str, required=True)

request_dd_single = reqparse.RequestParser()
request_dd_single.add_argument("location", type=str, required=True)
request_dd_single.add_argument("date", type=str, required=True)


#### Token Generator ####

def token_required(function):

    """ Creates a warper function for functions that require some sort of token validation.
    The token is decoded using the public id and secret key, if the token is ok the inner function
    will resume.
    """
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


class User(Resource):

    """ This class is used for user generation and checking. There are simple validation procedures
    for e-mails using regex. The password is hashed with pbkdf2:sha256 method and a public id is
    generated.
    --- GET ---
    Inputs:
    1. E-mail
    Returns the user info. This is used for testing and will require admin privilages in the future.
    TODO
    1. Make GET return everything about the user. Make it require both token and admin acess of the user that
    is making the request
    --- POST ---
    Inputs:
    1. E-mail
    2. Password
    Creates the user in the database.
    TODO
    1. Make a validation portion that checks if the e-mail exits in the database before commiting.
    """

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

    """ User login function that checks the password and e-mail before returning a token. The
    token lasts for 90 minutes before it expires.
    --- GET ---
    Inputs:
    1. Authorization
    """

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

class DDRequestRange(Resource):

    """ Class returns degree data for a selected date range & location. It first looks into the
    database for the required data. If the data isnt available, it requests it by a API function,
    returns it and updates the database. The limitation of the API call is -7 days.
    --- GET ---
    Inputs:
    1.Location 
    2.Date_one "%Y-%m-%d"
    3.Date_two "%Y-%m-%d"
    """

    def __init__(self):
        args = request_dd_args.parse_args()
        self.location = args["location"]
        self.date_one = args["date_one"]
        self.date_two = args["date_two"]

    def get(self):
        """TODO 
        1. Create a link to the database, so that the get request checks
        if the data is available in the database before it sends out the request
        if no the data should be requested and the database updated with it.
        2. Create validation on the date_one and date_two, so that its within 7 days
        """
        ##### Date validation #####

        try:
            date_one = datetime.strptime(self.date_one, "%Y-%m-%d")
            date_two = datetime.strptime(self.date_two, "%Y-%m-%d")
        except ValueError:
            logging.error("Dates have the wrong format")
            return {"error" : "Date needs to have the following format yyyy-mm-dd"}


        COLUMN_LIST = ['datetime', 'temp_c',
                       'CDD_10_5', 'CDD_15_5', 'CDD_18_5',
                       'HDD_10_5', 'HDD_15_5', 'HDD_18_5']

        return_data = pd.DataFrame(columns=COLUMN_LIST)

        for day_instance in range((date_two - date_one).days):
            
            start_day = date_one + timedelta(days=day_instance)
            end_day = start_day + timedelta(days=1)

            ### Try to find data in database ###
            try: 

                sql_query = f"SELECT * FROM degree_data_table WHERE '{start_day.date()}' < datetime "\
                            f"AND '{end_day.date()}' > datetime AND location_id == "\
                            f"(SELECT id FROM location_table WHERE location == '{self.location}')"

                db_data = db.session.execute(sql_query).fetchall()

                dd_data = pd.DataFrame(db_data, columns = ['index', 'location_id', 'datetime', 'temp_c',
                                                           'CDD_10_5', 'CDD_15_5', 'CDD_18_5',
                                                           'HDD_10_5', 'HDD_15_5', 'HDD_18_5'])
                dd_data = dd_data[COLUMN_LIST]
                return_data = return_data.append(dd_data)
            except:
                ### If the data is not in the database, request it via API and calculate the DD
                ### free version of the API is limited to last 7 days
                current_time = datetime.now()
                if (start_day - current_time) < timedelta(days=7):
                    api_data = GetWeatherDDData(self.location, start_day, start_day).generate_dd()

                    if bool(api_data):
                        return_data = return_data.append(api_data)
                        ## Update the DB ##
                        UpdateDB(api_data)._populate_tables()
                else:
                    logger.error("Data request out of date range.")
                    return {f"error": "Date : {start_day} is out of date range"}

        return_data = return_data.reset_index().to_dict(orient="index")
        
        return {'status': 'ok', 'json_data': return_data}

class DDRequestSingleDay(Resource):

    """ Class returns degree data for a selected date  & location. It first looks into the
    database for the required data. If the data isnt available, it requests it by a API function,
    returns it and updates the database. The limitation of the API call is -7 days.
    --- GET ---
    Inputs:
    1.Location 
    2.Date "%Y-%m-%d"
    """

    def __init__(self):
        args = request_dd_single.parse_args()
        self.date = args["date"]      
        self.location = args["location"]

    def get(self):
        
        COLUMN_LIST = ['datetime', 'temp_c',
                       'CDD_10_5', 'CDD_15_5', 'CDD_18_5',
                       'HDD_10_5', 'HDD_15_5', 'HDD_18_5']


        try:
            date = datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            logging.error("Dates have the wrong format")
            return {"error" : "Date needs to have the following format yyyy-mm-dd"}

        try: 
            end_day = date + timedelta(days=1)
            sql_query = f"SELECT * FROM degree_data_table WHERE '{date.date()}' < datetime "\
                        f"AND '{end_day.date()}' > datetime AND location_id == "\
                        f"(SELECT id FROM location_table WHERE location == '{self.location}')"
            print(sql_query)
            db_data = db.session.execute(sql_query).fetchall()

            dd_data = pd.DataFrame(db_data, columns = ['index', 'location_id', 'datetime', 'temp_c',
                                                        'CDD_10_5', 'CDD_15_5', 'CDD_18_5',
                                                        'HDD_10_5', 'HDD_15_5', 'HDD_18_5'])
            return_data = dd_data[COLUMN_LIST]
        
        except:
                ### If the data is not in the database, request it via API and calculate the DD
                ### free version of the API is limited to last 7 days
                current_time = datetime.now()
                if (date - current_time) < timedelta(days=7):
                    api_data = GetWeatherDDData(self.location, date, date).generate_dd()

                    if bool(api_data):
                        return_data = api_data[COLUMN_LIST]
                        ## Update the DB ##
                        UpdateDB(api_data)._populate_tables()
                else:
                    logger.error("Data request out of date range.")
                    return {f"error": "Date : {start_day} is out of date range"}

        return_data = return_data.reset_index().to_dict(orient="index")

        return {'status': 'ok', 'json_data': return_data}
        

#### Endpoints ####

api.add_resource(User, "/user")
api.add_resource(UserLogin, "/login")
api.add_resource(DDRequestRange, "/degree_data")
api.add_resource(DDRequestSingleDay, "/single_degree_data")

if __name__ == "__main__":
    app.run(debug=True)
    #db.create_all()
    # admin = UserTable(public_id="admin", e_mail="admin@example.com", password="12345678", admin= 1)
    # location = LocationTable(location = "London")
    # db.session.add(location)
    # db.session.commit()