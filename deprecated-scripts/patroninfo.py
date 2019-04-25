import secrets
import requests
import json

# Function to get sierra api/token via secrets file reference
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v4/token"
    # Create header with  API key from secrets.py
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    # Get response info
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    # Create var to hold the response data and return
    active_patrons_token = json_response["access_token"]
    return active_patrons_token

activepatrons = open("activepatrons.json", "r")
activejson = json.load(activepatrons)
write_file = open("checkoutinfo.json", "w")

write_file.write('{ "entries": [ \n')

for item in activejson["entries"]:
    id = item["id"]
    
    header_text = {"Authorization": "Bearer " + get_token()}
    
    # Prime loop 
    loop = True
    while loop == True and id<200000:

        # URL to find checkout info 
        checkout_url = "https://catalog.chapelhillpubliclibrary.org:443/iii/sierra-api/v4/patrons/" + str(id) + "/checkouts?fields=dueDate%2CnumberOfRenewals"
        request = requests.get(checkout_url, headers=header_text)
        # Stop looping when the requests sends an error code/doesn't connect
        if request.status_code != 200:
            break
        
        # Counter to find slice start point 
        counter = 1
        for letter in request.text:
            if letter == '[':
                break
            counter += 1
            
        # Slice off the beginning and ends of json to allow for combining all data
        sliced_json = request.text[counter:-2]
        if sliced_json == "":
           break
        else:   
            # write to csv?
            # sliced_json = sliced_json.replace("{", "")
            # sliced_json = sliced_json.replace("}","")
            # sliced_json = sliced_json.replace('"', "")
            # sliced_json = sliced_json.replace(":",",")
            # sliced_json =sliced_json.replace(",", ", ")
            # sliced_json = sliced_json.replace("https, ", "https:")
            # print(sliced_json[0:-1] + sliced_json[-1])
            sliced_json = sliced_json.replace("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v4/patrons/checkouts/", "")
            write_file.write(sliced_json) 
            write_file.write(',\n')
        loop = False

write_file.write(']}')

