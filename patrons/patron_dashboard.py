# import required library for accessing Sierra with authorization
import requests
import json
import csv
import datetime

# set present date equal to 'now' variable
now = datetime.datetime.now()

# function that gets the authentication token
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/token"
    header = {"Authorization": "Basic NVZuT3lhZXltczdUWUFsWnJnVDQrV0MyK2ZaUDpyRjBpaUBDVyF0bThMTGw4", "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token

def create_csv(x):
    id = 100010
    exp_counter = 0
    
    while True:
        
        url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/patrons?limit=2000&deleted=false&fields=expirationDate,addresses,names,emails&id=["+str(id)+",]"
        request = requests.get(url, headers={
                    "Authorization": "Bearer " + get_token()
                })
                
        if request.status_code != 200:
            return exp_counter
                
        jfile= json.loads(request.text)
        
        
        for entry in jfile["entries"]:
            try:
                row = []
                expy = int(entry["expirationDate"].split('-')[0])
                expm = int(entry["expirationDate"].split('-')[1])
                expd = int(entry["expirationDate"].split('-')[2])
                converted_date = datetime.datetime(expy,expm,expd)
                if int(converted_date <= now):
                    # print(entry)
                    row.append(entry["names"][0])
                    row.append(entry["addresses"][0]['lines'])
                    row.append(entry["emails"][0])
                    row.append(entry["expirationDate"])
                    x.writerow(row)
                    exp_counter += 1
            except KeyError:
                continue
        
        id = jfile["entries"][-1]["id"] + 1
        
        print(id)
        
patron_activity = open('expired_patrons.csv', 'w')
csvwriter = csv.writer(patron_activity)
csvwriter.writerow(['names','addresses','emails','expirationDate'])
csvwriter.writerow(['expired cards:', create_csv(csvwriter)])
patron_activity.close()