import logging
from flask_restful import reqparse, Resource
from src.database import db
from datetime import datetime, timedelta
import pandas as pd
from src.services.data_requester import GetWeatherDDData, UpdateDB

#### Logger configuration ####
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_handler = logging.FileHandler(r"log\dd_range.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formater)


request_dd_args = reqparse.RequestParser()
request_dd_args.add_argument("location", type=str, required=True)
request_dd_args.add_argument("date_one", type=str, required=True)
request_dd_args.add_argument("date_two", type=str, required=True)


class DDRequestRange(Resource):

    """ Class returns degree data for a selected date range & 
    location. It first looks into the database for the required
    data. If the data isnt available, it requests it by a API
    function, returns it and updates the database. The limitation
    of the API call is -7 days.
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
        1. Create a link to the database, so that the get request 
        checks if the data is available in the database before it
        sends out the request if no the data should be requested
        and the database updated with it.
        2. Create validation on the date_one and date_two, so that
        its within 7 days
        """
        ##### Date validation #####

        try:
            date_one = datetime.strptime(self.date_one, "%Y-%m-%d")
            date_two = datetime.strptime(self.date_two, "%Y-%m-%d")
        except ValueError:
            msg = ("Date needs to have the" 
                   "following format yyyy-mm-dd")
            
            logging.error("Dates have the wrong format")
            return {"error" : msg}


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

                dd_data = pd.DataFrame(db_data,
                                       columns = ['index',
                                                  'location_id',
                                                  'datetime',
                                                  'temp_c',
                                                  'CDD_10_5',
                                                  'CDD_15_5',
                                                  'CDD_18_5',
                                                  'HDD_10_5',
                                                  'HDD_15_5',
                                                  'HDD_18_5'])
                dd_data = dd_data[COLUMN_LIST]
                return_data = return_data.append(dd_data)
            except:
                # If the data is not in the database,
                # request it via API and calculate the DD
                # free version of the API is limited to
                # last 7 days
                current_time = datetime.now()
                if (start_day - current_time) < timedelta(days=7):
                    api_data = GetWeatherDDData(self.location,
                                                start_day,
                                                start_day
                                                ).generate_dd()

                    if bool(api_data):
                        return_data = return_data.append(api_data)
                        ## Update the DB ##
                        UpdateDB(api_data)._populate_tables()
                else:
                    logger.error("Data request out of date range.")
                    return {f"error": "Date : {start_day} is out of date range"}

        return_data = return_data.reset_index().to_dict(orient="index")
        
        return {'status': 'ok', 'json_data': return_data}
