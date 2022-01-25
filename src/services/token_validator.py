from functools import wraps
from flask import request
import jwt
from src.database import UserTable
from src.config.configuration import SECRET_KEY


def token_required(function):

    """ Creates a warper function for functions that require some sort of token validation.
    The token is decoded using the public id and secret key, if the token is ok the inner function
    will resume.
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        token = None
        print("Token check is running!")
        
        if "x-acess-token" in request.headers:
            token = request.headers["x-acess-token"]
        if not token:
            return {"error" : "Token is missing"}, 401
        
        #try:
        data = jwt.decode(token, key = SECRET_KEY)
        # data = data.decode("utf-8")
        print(data["public_id"])

        # current_user = UserTable.query.filter_by(public_id = data["public_id"]).first()
        # rows = session.query(Model.name).filter(Model.age >= 20).all()
        try:
            current_user = UserTable.query.filter(UserTable.public_id == data["public_id"]).first()
            print(type(current_user))
            print(current_user.e_mail)
        except:
           return {"message" : "Token is invalid"}, 401
        return function(*args, **kwargs)
    return decorated


if __name__ == "__main__":
    token =r'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiIwYzZmN2E5Ni1hNDVkLTQ0M2UtODBlMy1hOGVjM2EzODkyMjIiLCJleHAiOjE2NDMwNDQwOTN9.W5mtZeaaxH5AyuByde_ulksS1xGtoTcTadUALtp9XUo'
    data = jwt.decode(token, SECRET_KEY)
    print(data)