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
        
        try:
            data = jwt.decode(token, key = SECRET_KEY)
            current_user = UserTable.query.filter(UserTable.public_id == data["public_id"]).first()
        except:
           return {"message" : "Token is invalid"}, 401
        return function(current_user.e_mail,*args, **kwargs)
    return decorated


if __name__ == "__main__":
    token =''
    data = jwt.decode(token, SECRET_KEY)
    print(data)