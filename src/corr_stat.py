import logging
import ast
import json
from flask_restful import reqparse, Resource
from src.database import db
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
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
corr_analysis_parms.add_argument("location", location="json")

class DDCorelationAnalysis(Resource):
    
    def __init__(self):
        
        args = corr_analysis_parms.parse_args()
        self.args = dict(args)
        print(self.args)
        self.consumption = self._custom_type_validator(self.args["consumption"])
        self.period = self._custom_type_validator(self.args["period"])
        self.location = self.args["location"]
        
    def _custom_type_validator(self, input_parameter):
        
        if isinstance(input_parameter, (dict, str)):
            return input_parameter
        else:
            msg = ("Wrong data type - the inputs"
                   " have to be in a json format")
            return {"msg": msg}
    
    
    def get(self):
        
        self.consumption = ast.literal_eval(self.consumption)
        self.period = ast.literal_eval(self.period)
        
        df = pd.DataFrame.from_dict({"consumption" : self.consumption,
                                     "period" : self.period})
        
        start_day = min(df["period"])
        end_day = max(df["period"])
        
        df["period"] = pd.to_datetime(df["period"])
        print(df)
        df = df.set_index("period")
                                    
      
        COLUMNS_DATA = ['datetime',
                        'CDD_10_5',
                        'CDD_15_5',
                        'CDD_18_5',
                        'HDD_10_5',
                        'HDD_15_5',
                        'HDD_18_5']
        
        try: 

            sql_query = f"SELECT datetime, CDD_10_5, CDD_15_5, CDD_18_5,"\
                        f"HDD_10_5, HDD_15_5, HDD_18_5 " \
                        f"FROM degree_data_table WHERE '{start_day}' < datetime "\
                        f"AND '{end_day}' > datetime AND location_id == "\
                        f"(SELECT id FROM location_table WHERE location == '{self.location}')"

            db_data = db.session.execute(sql_query).fetchall()
            
            dd_data = pd.DataFrame(db_data,
                                   columns = COLUMNS_DATA)
        except:
            print("Nope")
            
               
        dd_data["datetime"] = pd.to_datetime(dd_data["datetime"])
        
        dd_data = dd_data.set_index("datetime")
        
        daily_dd_data = dd_data.resample("D").sum()
        
        final_df = df.join(daily_dd_data, how="right")
        print(final_df)
        
        # for i in final_df.columns:
        #     correlations = {}
        #     if i != "consumption":
        #         print(i)
        #         correlation = final_df["consumption"].corr(final_df[i])
        #         correlations[i:correlation]
        # print(correlations)
        final_df["consumption"] = pd.to_numeric(final_df["consumption"])
        x = final_df["consumption"].corr(final_df["HDD_15_5"], method="pearson")
        print(x)
        # Create a R2 calculation and generate and return the best degree data with the R2
        return {"ok" : "Well this went well"}