import re
import uuid
import jwt
import logging
from flask_restful import reqparse, Resource
from werkzeug.security import generate_password_hash,check_password_hash
from src.database import UserTable, db
from flask import request
from datetime import datetime, timedelta

#### Logger configuration ####
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formater = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(r"log\user.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formater)


create_user_args = reqparse.RequestParser()
create_user_args.add_argument("e_mail", type=str)
create_user_args.add_argument("password", type=str)


class CreateUser(Resource):

    """ This class is used for user generation and checking. 
    There are simple validation procedures for e-mails using
    regex. The password is hashed with pbkdf2:sha256 method 
    and a public id is generated.
    """

    REGEX_E_MAIL_VALIDATION = re.compile(r"([A-Za-z0-9]+[.-_])" \
                                         r"*[A-Za-z0-9]+@[A-Za-" \
                                         r"z0-9-]+(\.[A-Z|a-z]{2,})+")

    def __init__(self):
        args = create_user_args.parse_args()
        self.e_mail = self._email_validator(args["e_mail"])
        self.password = generate_password_hash(args["password"],
                                               method="pbkdf2:sha256")
        self.public_id = str(uuid.uuid4())
        self.admin = False

    def get(self):
        print(self.e_mail)
        return {"user" : self.e_mail}, 201

    def post(self):

        if len(self.password) < 6:
            return {"error" : "Password is too short!"}, 400   

        if UserTable.query.filter_by(e_mail=self.e_mail).first() is not None:
            return {"error": "E-mail already taken!"}, 409


        new_user = UserTable(public_id=self.public_id,
                             e_mail = self.e_mail,
                             password = self.password,
                             admin = self.admin
                            )
        db.session.add(new_user)
        db.session.commit()

        return {"message" : "New user created!",
                "user": self.e_mail
            }, 201

    ## Future changes: move to seperate modul
    def _email_validator(self, email): 
        if re.fullmatch(self.REGEX_E_MAIL_VALIDATION, email):
            return email
        else:
            logger.info("Regex improvment data")
            return {"error" : "E-mail is not valid!"}, 400

class UserLogin(Resource):

    """ User login function that checks the password 
    and e-mail before returning a token. The
    token lasts for 90 minutes before it expires.
    """
    
    def __init__(self):
        self.auth = request.authorization

    def get(self):

        username = self.auth.username
        print(username)

        if not self.auth or not self.auth.username or not self.auth.password:
            return {"error" : "Could not verify!"}, 401

        user = UserTable.query.filter_by(e_mail=self.auth.username).first()
        if not user:
            return {"error" : "Could not verify!"}, 401


        if check_password_hash(user.password, self.auth.password):
            token = jwt.encode({"public_id" : user.public_id,
                                "exp" : datetime.utcnow() + timedelta(minutes=90) 
                                },"secret", algorithm="HS256")
            return {"token" : token}

        return {"error" : "Could not verify!"}, 401


