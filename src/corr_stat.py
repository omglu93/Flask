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
        self.consumption = self.args["consumption"]
        self.period = self.args["period"]
        self.location = self.args["location"]
        
    def _date_validator(self, input_date):
        
        sql_query = f"SELECT datetime FROM degree_data_table "\
                    f"WHERE datetime = '{input_date}'"
        return db.session.execute(sql_query).fetchall()
      
    def get(self):
        

        # Conversion to dic and pd.DataFrame
        
        self.consumption = ast.literal_eval(self.consumption)
        self.period = ast.literal_eval(self.period)
        
        # Validation of the input size
        print(len(self.period))
        print(len(self.consumption))
        if len(self.consumption) != len(self.period):
            return {"error": "Input parameters have different sizes"}, 400
        
        
        
        df = pd.DataFrame.from_dict({"consumption" : self.consumption,
                                     "period" : self.period})
        
        # Validation of input dates
        for period in df["period"]:
            
            if self._date_validator(period) is None:
                return {"error" : "Date requested is out of range of DB"}, 400
            
        start_day = min(df["period"])
        end_day = max(df["period"])
        
        df["period"] = pd.to_datetime(df["period"])
        
        
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
                        f"AND '{end_day}' >= datetime AND location_id == "\
                        f"(SELECT id FROM location_table WHERE location == '{self.location}')"

            db_data = db.session.execute(sql_query).fetchall()
            
            dd_data = pd.DataFrame(db_data,
                                   columns = COLUMNS_DATA)
        except:
            return {"error" : "Data retrival failed"}, 400
            
               
        dd_data["datetime"] = pd.to_datetime(dd_data["datetime"])
        
        dd_data = dd_data.set_index("datetime")
        
        daily_dd_data = dd_data.resample("D").sum()
        
        final_df = df.join(daily_dd_data, how="right")
        print(final_df)
        
        final_df["consumption"] = pd.to_numeric(final_df["consumption"])
        
        max_correlation = 0
        max_dd = ""
        for dd in final_df.columns[1:]:
            x = final_df["consumption"].corr(final_df[dd], method="pearson")
            r_sq = x**2
            
            if r_sq > max_correlation:
                max_correlation = r_sq
                max_dd = dd
                
        print(max_correlation, max_dd)
        # Create a R2 calculation and generate and return the best degree data with the R2
        return {"ok" : "Well this went well"}