from flask import Flask
from src.database import db
from flask_restful import Api
from src.user import CreateUser, UserLogin, UserDetails
from src.dd_range import DDRequestRange
from src.dd_single import DDRequestSingleDay
from src.config.configuration import *


def create_app(test_config=None):

    app = Flask(__name__,
    instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=SECRET_KEY,
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI,
            SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
        )
    
    else:
        app.config.from_mapping(test_config)
    
    db.app = app
    db.init_app(app)
    api = Api(app)

    endpoint_prefix = "/api/v1"

    api.add_resource(CreateUser, endpoint_prefix + "/create-user")
    api.add_resource(UserLogin, endpoint_prefix + "/login")
    api.add_resource(UserDetails, endpoint_prefix + "/user-details")
    api.add_resource(DDRequestRange, endpoint_prefix + "/range-degree-data")
    api.add_resource(DDRequestSingleDay, endpoint_prefix + "/single-degree-data")

    
    return app