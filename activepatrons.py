import requests
import datetime
import json
import csv
import traceback
# Import secrets file
import secrets


# Function to create the save file vars
def create_save_files():
    # Link to CHFS directory
    unpublished_file = '//CHFS/Shared Documents/OpenData/datasets/staging/activepatrons.json'
    # Open file to write
    patrons = open(unpublished_file, 'w')
    return patrons

# Function to get the date
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

# Function to get the API token, via code Steven created
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/token"
    # Get the API key from secrets.py
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    # Create var to hold the response data
    active_patrons_token = json_response["access_token"]
    return active_patrons_token

# Function to fetch the data and write to file
def fetch_data():
    
    patrons = create_save_files()
    date_range = get_date()
    
    patrons.write('{ "entries": [ \n')
    
    # Save header in var, change api key as needed (for now)
    header_text = {"Authorization": "Bearer " + get_token()}

    # Set looping vars
    i = 0
    loop=True
    
    # Loop goes through records up to i
    while loop == True:
        # Request the api data at url
        request = requests.get("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v4/patrons/?limit=2000&offset=" + str(i) + "&fields=addresses,updatedDate&updatedDate=" + str(date_range), headers=header_text)
        
        # Testing
        # print(i)
        
        # Stop looping when the requests sends an error code/doesn't connect
        if request.status_code != 200:
            break
        elif i != 0:
            # adds a comma and newline for better organization and format
            patrons.write(',\n')
        
        # Counter to find slice start point 
        # copy Steven for this bit of code
        counter = 1
        for letter in request.text:
            if letter == '[':
                break
            counter += 1
            
    
        # Slice off the beginning and ends of json to allow for combining all data
        sliced_json = request.text[counter:-2]

        # Write data to patron json file 
        patrons.write(sliced_json)
        # Increment i 
        i = i + 2000
        
    patrons.write(']}')
    

# Main function, call fetch_data()        
def main(): 
    errors = open("activepatrons_error_log.txt", "w")
    try:
        fetch_data()
    except Exception as exc:
        errors.write(traceback.format_exc())
main()
