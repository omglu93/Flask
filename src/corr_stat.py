import logging
import ast
from flask_restful import reqparse, Resource
from src.database import DegreeDataTable, db
import pandas as pd


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
    """This endpoint/class allows the user to send in energy consumption
    data, dates of the consumption and location of the consumption. Afterwards,
    the function evaluates the data against the degree database and finds the
    greatest correlation between the degree data groups. This is then returned
    to the user.

    Inputs:
        period (str): period of the consumption
        consumption (str): the consumption of the coresponding period
        location (str): location of the coresponding consumpion

    Returns:
        json (json): provides the maximum coefficient of determination and its
        coresponding degree data group.
    """
    COLUMNS_DATA = ['datetime',
                    'CDD_10_5',
                    'CDD_15_5',
                    'CDD_18_5',
                    'HDD_10_5',
                    'HDD_15_5',
                    'HDD_18_5'] 
    
    def __init__(self):
        
        args = corr_analysis_parms.parse_args()
        self.args = dict(args)
        self.consumption = self.args["consumption"]
        self.period = self.args["period"]
        self.location = self.args["location"]
        
    def _date_validator(self, input_date : str):
        
        """Validator that checks if the database
        has data coresponding to the requested date

        Args:
            input_date (str): loop feed data from a pandas df

        Raises:
            Exception: handles instances without date and returns
            information as a json.
        """
        
        if len(input_date) < 11:
            input_date = input_date + " 00:00"
        sql_data = DegreeDataTable.query.filter_by(datetime = input_date).count()
        
        if sql_data > 0:
            pass
        else:
            raise Exception(f"Date {input_date} not in database")
        
    def get(self):
        

        # Conversion to dic and pd.DataFrame
        
        self.consumption = ast.literal_eval(self.consumption)
        self.period = ast.literal_eval(self.period)
        
        # Validation of the input size
        if len(self.consumption) != len(self.period):
            return {"error": "Input parameters have different sizes"}, 400
              
        
        df = pd.DataFrame.from_dict({"consumption" : self.consumption,
                                     "period" : self.period})
        
        # Validation of input dates
        
        try:
            for period in df["period"]:
                self._date_validator(period)
        except Exception as e:
            msg = str(e)
            return {"error" : msg}, 400
                                                
        try: 
            
            start_day = min(df["period"])
            end_day = max(df["period"])

            sql_query = f"SELECT datetime, CDD_10_5, CDD_15_5, CDD_18_5,"\
                        f"HDD_10_5, HDD_15_5, HDD_18_5 " \
                        f"FROM degree_data_table WHERE '{start_day}' < datetime "\
                        f"AND '{end_day}' >= datetime AND location_id == "\
                        f"(SELECT id FROM location_table WHERE location == '{self.location}')"

            db_data = db.session.execute(sql_query).fetchall()
            
            dd_data = pd.DataFrame(db_data,
                                   columns = self.COLUMNS_DATA)
        except:
            return {"error" : "Data retrival failed"}, 400
        
        # Start of the dataframe operations
        try:
            df["period"] = pd.to_datetime(df["period"])
            df = df.set_index("period")
            
            dd_data["datetime"] = pd.to_datetime(dd_data["datetime"])
            
            dd_data = dd_data.set_index("datetime")
            
            daily_dd_data = dd_data.resample("D").sum()
            
            final_df = df.join(daily_dd_data, how="right")
            
            final_df["consumption"] = pd.to_numeric(final_df["consumption"])
        except:
            return {"error": "Error while processing data"}
        
        try:
            max_correlation = 0
            max_dd = ""
            for dd in final_df.columns[1:]:
                x = final_df["consumption"].corr(final_df[dd], method="pearson")
                r_sq = x**2
                
                if r_sq > max_correlation:
                    max_correlation = r_sq
                    max_dd = dd
        except:
            return {"error" : "Error in the calculation of the " 
                    "coefficient of determination"}
                
        print(max_correlation, max_dd)
        return {"best_correlation" : {max_dd : max_correlation}}