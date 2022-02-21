import logging
import json
from msilib.schema import ReserveCost
from flask_restful import reqparse, Resource
from src.database import db
from datetime import datetime, timedelta
import pandas as pd
from src.services.data_requester import GetWeatherDDData


#### Logger configuration ####
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(r"src\log\dd_corr_analysis.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formater)


corr_analysis_parms = reqparse.RequestParser()
corr_analysis_parms.add_argument("period", location="json")
corr_analysis_parms.add_argument("consumption", location="json")

class DDCorelationAnalysis(Resource):
    
    def __init__(self):
        
        args = corr_analysis_parms.parse_args()
        self.periods = self._custom_type_validator(args["period"])
        self.consumption = self._custom_type_validator(args["consumption"])
    
    def _custom_type_validator(self, input_parameter):
        
        if isinstance(input_parameter, (dict, str)):
            return input_parameter
        else:
            msg = ("Wrong data type - the inputs"
                   " have to be in a json format")
            return {"msg": msg}
    
    
    def get(self):
        
        #df = pd.DataFrame(columns=["period", "consumption"])
        
        print(self.periods)
        print(type(self.periods))        
        # period = dict(self.periods)
        # consumption = dict(self.consumption)
        # for date, consumption in zip(period, consumption):
            
        #     print(date)
        #     print(consumption)
        #df = pd.DataFrame.from_dict(self.periods) 
        #### TODO Parase with zip both period and consumption in the dataframe
        
        return {"ok" : "Well this went well"}