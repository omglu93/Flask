import logging
from flask_restful import reqparse, Resource
from src.database import db
from datetime import datetime, timedelta
import pandas as pd
from src.services.data_requester import GetWeatherDDData, UpdateDB
from src.services.token_validator import token_required


#### Logger configuration ####
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(r"src\log\dd_single.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formater)


request_dd_single = reqparse.RequestParser()
request_dd_single.add_argument("location", type=str, required=True)
request_dd_single.add_argument("date", type=str, required=True)

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

    @token_required
    def get(user,self):
        
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