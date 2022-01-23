import requests
from requests.auth import HTTPBasicAuth
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)
BASE_URL = "http://127.0.0.1:5000/"

#### Create User -- POST ####
# create_user = {"e_mail": "omar@test.com", "password" : "omarjenajjaci"}

# data = requests.get(BASE_URL + "create-user", json = create_user)
# print(data.text)


#### Login User & Get Token ####

# data = requests.get(BASE_URL + "login", auth=HTTPBasicAuth("omar@omar.com", "omarjenajjaci"))
# print(data.text)
# print(data)


### DD Usage and getting daata ###

# ddr = {"location": "London", "date_one" : "2021-12-19", "date_two" : "2021-12-22"}
# data = requests.get(BASE_URL + "degree_data", json=ddr)
# #print(data.json())
# json_data = data.json()
# print(json_data['json_data'])

### DD single day ###

ddr = {"location": "London", "date" : "2021-12-19"}
data = requests.get(BASE_URL + "single_degree_data", json=ddr)
#print(data.json())
json_data = data.json()
print(json_data['json_data'])

