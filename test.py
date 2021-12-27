import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:5000/"

#### Create User -- POST ####
# create_user = {"e_mail": "omar@omar.com", "password" : "omarjenajjaci"}

# BASE_URL = "http://127.0.0.1:5000/"

# data = requests.post(BASE_URL + "create-user", json = create_user)
# print(data.text)


#### Login User & Get Token ####

# data = requests.get(BASE_URL + "login", auth=HTTPBasicAuth("omar@omar.com", "omarjenajjaci"))
# print(data.text)


### Token Usage and getting daata ###

