# import required library for accessing Sierra with authorization
import requests
import json
import csv
import datetime
import secrets

# set present date equal to 'now' variable
now = datetime.datetime.now()

# function that gets the authentication token
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/token"
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token

# function that creates a csv file and adds on expired patron's names, addresses, emails, and exp. date
def create_csv(writer, age_adder, p_counter, b_counter):
    # first id is 100010
    id = 100010

    log_file.write("Getting Access token for authentication. \n")
    token = get_token()
    log_file.write("Token retrieved.\n\n")
    
    log_file.write("Sending GET request, accessing 2000 id's at a time. \n")
    
    # loop until there are no more patron records (error code 200)
    while True:
        
        url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/patrons?limit=2000&deleted=false&fields=expirationDate,addresses,names,emails,birthDate,blockInfo&id=["+str(id)+",]"
        request = requests.get(url, headers={
                    "Authorization": "Bearer " + token
                })
                
        if request.status_code != 200:
            break
                
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
                    writer.writerow(row)
                else:
                    if entry["blockInfo"]["code"] != '-':
                        b_counter += 1
                    birth_year = int(entry["birthDate"].split('-')[0])
                    age_adder += (now.year - birth_year)
                    p_counter += 1
                    # print("age:", now.year - birth_year)
                    # print("total age:", age_adder)
                    # print("total:", p_counter)
            except KeyError:
                continue
        
        id_prev = id
        id = jfile["entries"][-1]["id"] + 1
        
        log_file.write("Records from id's " + str(id_prev) + " and on written to csv file, Accessing next page.\n")
        # print(id)
    
    return (age_adder/p_counter), b_counter

# create date variable
today = datetime.date.today()

# create variable for average age of all patrons
total_age = 0
    
# create counter for all unexpired patrons
patron_counter = 0

# create counter for blocked patrons
blocked_counter = 0

# throw an error if a "/logs" directory doesn't exist
try:
    log_file = open('logs/' + str(today) + '-expired_patrons.txt', 'w')
except:
    error_file = open('error.txt', 'w')
    error_file.write('ERROR - "logs" directory not found\n')
    error_file.close()
    
# open csv file for writing
log_file.write('Creating expired_patrons.csv file.\n')
expired_patrons = open('//CHFS/Shared Documents/OpenData/datasets/prestaging/expired_patrons.csv', 'w')
log_file.write('Creating patron_data.csv file.\n\n')
patron_data = open('//CHFS/Shared Documents/OpenData/datasets/prestaging/patron_data.csv', 'w')

# create a csvwriter object
exp_csvwriter = csv.writer(expired_patrons)
dashboard_csvwriter = csv.writer(patron_data)

# write a header & call the create_csv function
log_file.write('Writing header on expired_patrons file.\n')
exp_csvwriter.writerow(['names','addresses','emails','expirationDate'])
log_file.write('Writing header on patron_data file. \n\n')
dashboard_csvwriter.writerow(['average age','blocked patrons'])
avg_age, blocked_patrons = create_csv(exp_csvwriter, total_age, patron_counter, blocked_counter)
dashboard_csvwriter.writerow([avg_age,blocked_patrons])

log_file.write("\nAll expired patron data has been successfully written to expired_patrons.csv.\n")
log_file.write("Average age and blocked patron data has been successfully written to patron_data.csv.\n\n")
log_file.write(str(datetime.datetime.now()))

# close files
expired_patrons.close()
log_file.close()
