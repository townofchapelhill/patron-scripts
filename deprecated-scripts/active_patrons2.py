# import required library for accessing Sierra with authorization
import requests
import json
import secrets
import datetime
import csv

# function checks if a string is an ASCII (english characters only)
def is_ascii(s):
	return all(ord(c) < 128 for c in s)

# function that gets the authentication token
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/token"
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    # log_file.write("Sending POST request. \n")
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token
    
def get_date():
    now = str(datetime.date.today())
    # Add string to date to fix sierra syntax
    present_date_string = now + str("T00:00:00Z")
    # Get the date from a year ago and create string
    one_year_ago = str(datetime.date.today() - datetime.timedelta(days=365))
    old_date_string = one_year_ago + str("T00:00:00Z")
    # Create a date range string that fits into the api call format
    date_range = "[" + str(old_date_string) + "," + str(present_date_string) + "]"
    return date_range

# function that updates the patron json file
def update_patrons(writer):
    # loop through each URI, incrementing by the limit of 2,000 until all patron data accessed
    i = 0
    # log_file.write("Getting Access token for authentication. \n")
    token = get_token()
    date_range = get_date()
    # log_file.write("Token retrieved.\n\n")
    # log_file.write("Sending GET request, accessing 2000 records at a time. \n")
    
    while True:
        
        # set request variable equal to URI at i's index, showing fields: createdDate, names, barcodes, expirationDate and deleted is false
        request = requests.get("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/patrons/?limit=2000&offset=" + str(i) + "&fields=updatedDate&updatedDate=" + str(date_range), headers={
            "Authorization": "Bearer " + token
        })
        
        # stop looping when the requests sends an error code (reached current patron data)
        if request.status_code != 200:
            break
        
        jfile = json.loads(request.text)
        print(jfile)
        # loops through response data, appending categories of patron data
        # with matching column headers
        for entry in jfile["entries"]:
            try:
                row = []
                row.append(entry["id"])
                row.append(entry["updatedDate"])
                writer.writerow(row)
            except KeyError:
                row.append("")
                writer.writerow(row)
        
        # increment i by 2000 for the next 2000 records
        i_prev = i
        i += 2000
        log_file.write("Records from " + str(i_prev) + " and on written to csv file, Accessing next page.\n")
        
# create date variable
today = datetime.date.today()

# throw an error if a "/logs" directory doesn't exist
try:
    log_file = open('logs/' + str(today) + '-active_patrons.txt', 'w')
    log_file.write(str(datetime.datetime.now()))
except:
    error_file = open('error.txt', 'w')
    error_file.write('ERROR - "logs" directory not found\n')
    error_file.close()
    
# open a csv file for writing
log_file = open('active_patrons_log.txt', 'w')
log_file.write("\nCreating patrons.csv file.\n\n")
patrons = open('//CHFS/Shared Documents/OpenData/datasets/staging/activepatrons.csv', 'w')

# create csvwriter object
patron_csvwriter = csv.writer(patrons)

# write a header 
log_file.write('Writing header on patron file.\n')
patron_csvwriter.writerow(['ID', 'Updated Date'])

# call update function
update_patrons(patron_csvwriter)

# close files
log_file.write("\nAll patron data has been successfully written to patrons.csv.\n\n")
log_file.write(str(datetime.datetime.now()))
patrons.close()
# log_file.close()
print("done")