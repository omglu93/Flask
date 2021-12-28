import requests
from requests.auth import HTTPBasicAuth
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)
BASE_URL = "http://127.0.0.1:5000/"

#### Create User -- POST ####
#create_user = {"e_mail": "omar@omar.com", "password" : "omarjenajjaci"}

# BASE_URL = "http://127.0.0.1:5000/"

# data = requests.post(BASE_URL + "create-user", json = create_user)
# print(data.text)


#### Login User & Get Token ####

# data = requests.get(BASE_URL + "login", auth=HTTPBasicAuth("omar@omar.com", "omarjenajjaci"))
# print(data.text)


### DD Usage and getting daata ###

ddr = {"location": "London", "date_one" : "27-12-2021"}
data = requests.get(BASE_URL + "request-dd", json=ddr)
pp.pprint(json.loads(data.text))

