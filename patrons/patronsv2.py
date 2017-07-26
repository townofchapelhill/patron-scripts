# import required library for accessing Sierra with authorization
import requests
import json

# function that gets the authentication token]
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/token"
    header = {"Authorization": "Basic NVZuT3lhZXltczdUWUFsWnJnVDQrV0MyK2ZaUDpyRjBpaUBDVyF0bThMTGw4", "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    token = json_response["access_token"]
    return token
    
# function that updates the patron json file
def update_patrons():
    # loop through each URI, incrementing by the limit of 2,000 until all patron data accessed
    i = 0
    while True:
        
        print(i) # for testing purposes
        
        # set request variable equal to URI at i's index, showing fields: createdDate, names, barcodes, expirationDate and deleted is false
        request = requests.get("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v3/patrons?offset=" + str(i) + "&limit=2000&fields=createdDate,names,barcodes,expirationDate&deleted=false", headers={
            "Authorization": "Bearer " + get_token()
        })
    
        # stop looping when the requests sends an error code (reached current patron data)
        if request.status_code != 200:
            return False
        
        # slice off the beginning and ends of json to allow for combining all data
        sliced_json = request.text[38:-2]
    
        # append data to patron json file and add a newline each iteration for better organization
        patrons.write(sliced_json + ",\n")
        
        # increment i by 2000 for the next 2000 records
        i += 2000
    
    return True

# open a json file
patrons = open('patrons.json', 'a')

# if update is successful, close file
if update_patrons() == True:
    # brackets signal end of file
    patrons.write(']}')
    patrons.close()
else:
    print("done")