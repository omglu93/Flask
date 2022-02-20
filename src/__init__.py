from flask import Flask
from src.database import db
from flask_restful import Api
from src.user import CreateUser, UserLogin
from src.dd_range import DDRequestRange
from src.dd_single import DDRequestSingleDay
from src.corr_stat import DDCorelationAnalysis

def create_app(test_config=None):

    app = Flask(__name__,
    instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY="somekey",
            SQLALCHEMY_DATABASE_URI = "sqlite:///degree_data.db",
            SQLALCHEMY_TRACK_MODIFICATIONS = False
        )
    
    else:
        app.config.from_mapping(test_config)
    
    db.app = app
    db.init_app(app)
    api = Api(app)

    api.add_resource(CreateUser, "/create-user")
    api.add_resource(UserLogin, "/login")
    api.add_resource(DDRequestRange, "/degree_data")
    api.add_resource(DDRequestSingleDay, "/single_degree_data")
    api.add_resource(DDCorelationAnalysis, "/dd-corr")
    
    return app