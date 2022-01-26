from lib2to3.pgen2 import token
import requests
from requests.auth import HTTPBasicAuth
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)
endpoint_prefix = "api/v1/"
BASE_URL = "http://127.0.0.1:5000/" + endpoint_prefix

#### Create User -- POST ####
# create_user = {"e_mail": "omar@test.com", "password" : "omarjenajjaci"}

# data = requests.get(BASE_URL + "create-user", json = create_user)
# print(data.text)


#### Login User & Get Token ####

data = requests.get(BASE_URL + "login", auth=HTTPBasicAuth("omar@omar.com", "omarjenajjaci"))
json_data = data.json()
token = json_data['token']
print(token)


### DD Usage and getting daata ###
# token = "b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiIwYzZmN2E5Ni1hNDVkLTQ0M2UtODBlMy1hOGVjM2EzODkyMjIiLCJleHAiOjE2NDMwMzg5OTR9.miv24VJn2uFLZIgvR_wJzq42R0n3QZdAFrqdJMtK_zM'"
# ddr = {"location": "London", "date_one" : "2021-12-19", "date_two" : "2021-12-22"}
# data = requests.get(BASE_URL + "range-degree-data", json=ddr, headers={"x-acess-token" : token})
# json_data = data.json()
# print(json_data)

### DD single day ###

ddr = {"location": "London", "date" : "2021-12-19"}
data = requests.get(BASE_URL + "single-degree-data", json=ddr, headers={"x-acess-token" : token})
#print(data.json())
json_data = data.json()
print(json_data['json_data'])

