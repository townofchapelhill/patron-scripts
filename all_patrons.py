# import required library for accessing Sierra with authorization
import requests
import json
import secrets
import datetime

# function that gets the authentication token
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/token"
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    log_file.write("Sending POST request. \n")
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token
    
# function that updates the patron json file
def update_patrons():
    # loop through each URI, incrementing by the limit of 2,000 until all patron data accessed
    i = 0
    
    log_file.write("Getting Access token for authentication. \n")
    token = get_token()
    
    log_file.write("Token retrieved.\n\n")
    log_file.write("Sending GET request, accessing 2000 records at a time. \n")
    
    while True:
        
        # print(i) # for testing purposes
        
        # set request variable equal to URI at i's index, showing fields: createdDate, names, barcodes, expirationDate and deleted is false
        request = requests.get("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/patrons?offset=" + str(i) + "&limit=2000&fields=createdDate,names,barcodes,expirationDate,emails&deleted=false", headers={
            "Authorization": "Bearer " + token
        })
        
        # stop looping when the requests sends an error code (reached current patron data)
        if request.status_code != 200:
            break
        elif i != 0:
            # adds a comma and newline for better organization and format
            patrons.write(',\n')
        
        # counter looks for slice start point
        counter = 1
        for letter in request.text:
            if letter == '[':
                break
            counter += 1

        # slice off the beginning and ends of json to allow for combining all data
        sliced_json = request.text[counter:-2]
            
        # append data to patron json file
        patrons.write(sliced_json)
        
        # increment i by 2000 for the next 2000 records
        i_prev = i
        i += 2000
        log_file.write("Records from " + str(i_prev) + " and on written to json file, Accessing next page.\n")
        
# create date variable
today = datetime.date.today()

# throw an error if a "/logs" directory doesn't exist
try:
    log_file = open('logs/' + str(today) + '-all_patrons.txt', 'w')
    log_file.write(str(datetime.datetime.now()))
except:
    error_file = open('error.txt', 'w')
    error_file.write('ERROR - "logs" directory not found\n')
    error_file.close()
    
# open a json file & write a header
log_file.write("\nCreating patrons.json file.\n\n")
patrons = open('//CHFS/Shared Documents/OpenData/datasets/staging/patrons.json', 'w')
patrons.write('{ "entries": [ \n')

# call update function
update_patrons()

# brackets signal end of file
patrons.write(']}')
log_file.write("\nAll patron data has been successfully written to patrons.json.\n\n")
log_file.write(str(datetime.datetime.now()))
patrons.close()
log_file.close()
print("done")
