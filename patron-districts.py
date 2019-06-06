# import libraries
import requests
import secrets
import csv
import json
import re
import os
from datetime import datetime
from datetime import date

# Object used to store data to aid in transformation
class Patron(object):
    def __init__(self, id=None, pType=None, strAddress=None, city=None, state=None, zip=None, expDate=None, bDate=None, geoBound=None):
        self.id = ''
        self.pType = ''
        self.strAddress = ''
        self.city = ''
        self.state = ''
        self.zip = ''
        self.expDate = ''
        self.bDate = ''
        self.geoBound = ''

# GETs all patron records from Sierra
def get_all_patrons():
    all_patrons = []
    iterator = 0
    active_patrons_token = get_token()

    # while loop to iterate through database, GET-ing 2000 records per query
    while True:
        get_header_text = {"Authorization": "Bearer " + active_patrons_token}
        get_request = requests.get("https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/patrons?offset=" + str(iterator) + "&limit=2000&fields=patronType,addresses,expirationDate,birthDate&deleted=false", headers=get_header_text)
        data = json.loads(get_request.text)
        try:
            for i in data['entries']:
                all_patrons.append(i)
        except:
            parse_data(all_patrons)
            break

# Function to parse and transform retrieved data as necessary
def parse_data(all_patrons):
    parsed_patrons = []
    counter = 1
    for entry in all_patrons:
        # create new instance of "Patron" object to hold info from each record
        new_patron = Patron()
        new_patron.id = counter
        new_patron.pType = entry['patronType']
        # try/catch prevents script failure from records with missing data
        try:
            new_patron.expDate = entry['expirationDate']
            new_patron.bDate = entry['birthDate']
            # address must be split into seperate columns to satisfy Open Data Geo-processors
            split_address = entry['addresses'][0]['lines'][1].split(' ')
            new_patron.strAddress = entry['addresses'][0]['lines'][0]
            # Conditional to handle "split_address" list differences caused by city name
            if split_address[0] == 'CHAPEL':
                city = split_address[0] + ' ' + split_address[1]
                new_patron.city = city
                new_patron.state = split_address[2]
                new_patron.zip = split_address[3]
            else:
                new_patron.city = split_address[0]
                new_patron.state = split_address[1]
                new_patron.zip = split_address[2]
        except:
            pass
        counter += 1
        # store "Patron" as a dictionary
        parsed_patrons.append(new_patron.__dict__)
    
    # transforms expDate and bDate to requested values
    for patron in parsed_patrons:
        today = date.today()
        days_in_year = 365.2425
        try:
            # determines bDate down to the day
            parsed_bDate = date(int(patron['bDate'][0:4]), int(patron['bDate'][5:7]), int(patron['bDate'][8:10]))
            age = int((today - parsed_bDate).days / days_in_year)
            if age >= 18:
                patron['bDate'] = "Adult"
            else:
                patron['bDate'] = "Juvenile"
        except:
            continue
        
        try:
            # determines expDate down to the day
            parsed_expDate = date(int(patron['expDate'][0:4]), int(patron['expDate'][5:7]), int(patron['expDate'][8:10]))
            active = float((parsed_expDate - today).days / days_in_year)
            if active > 0.0 and active < 3.0:
                patron["expDate"] = "Active"
            else:
                patron["expDate"] = "Inactive"
        except:
            continue
    
    # call next function, pass "parsed_patrons"
    check_geoBoundary(parsed_patrons)

# checks for whether or not a patron lives within Chapel Hill, within Orange County, or outside of county
# Additionally, dumps rejected addresses into a CSV to assist Library staff
def check_geoBoundary(parsed_patrons):
    checked_addresses = []
    skipped_addresses = []
    for patron in parsed_patrons:
        # format address to play nice with GIS
        full_address_string = patron['strAddress'] + '%2C+' + patron['city'] + '%2C+' + patron['state'] + '+' + patron['zip']
        try:
            # returns geo coordinates
            get_request = requests.get('https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/find?text=' + full_address_string + '&f=pjson')
            data = json.loads(get_request.text)
            xCoord = data['locations'][0]['feature']['geometry']['x']
            yCoord = data['locations'][0]['feature']['geometry']['y']
            if len(data['locations'][0]) == 0:
                skipped_addresses.append(patron)
        except:
            skipped_addresses.append(patron)
            continue

        # Checks within Chapel Hill GeoBoundary
        city_limits_request = requests.get("https://gisweb.townofchapelhill.org/arcgis/rest/services/MapServices/tochBoundary/MapServer/0/query?geometry=" + str(xCoord) + "%2C" + str(yCoord) + "&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelWithin&returnGeometry=false&outSR=102100&returnCountOnly=true&f=json")
        try:
            city_limits_data = json.loads(city_limits_request.text)
        except:
            pass
        try: 
            if city_limits_data['count'] == 1:
                patron['geoBound'] = 'Within Chapel Hill'
            else:
                # Checks within Orange County GeoBoundary
                county_limits_request = requests.get("https://gisweb.townofchapelhill.org/arcgis/rest/services/MapServices/ToCH_OrangeCo_CombinedLimits/MapServer/0/query?geometry=" + str(xCoord) + "%2C" + str(yCoord) + "&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelWithin&returnGeometry=false&outSR=102100&returnCountOnly=true&f=json")
                county_limits_data = json.loads(county_limits_request.text)
                if county_limits_data['count'] == 1:
                    patron['geoBound'] = 'Within Orange County'
                else:
                    patron['geoBound'] = 'Outside Orange County'
            checked_addresses.append(patron)
        except:
            skipped_addresses.append(patron)
            continue
    
    # call CSV writer function
    write_csv(checked_addresses, skipped_addresses)


# writes the final csv
def write_csv(checked_addresses, skipped_addresses):
    # writes CSV that's pushed to portal
    with open("//CHFS/Shared Documents/OpenData/datasets/staging/all_patrons_new.csv", "w+") as update_patrons:
        fieldnames = checked_addresses[0].keys()
        csv_writer = csv.DictWriter(update_patrons, fieldnames=fieldnames, extrasaction='ignore', delimiter=',')
        
        if os.stat('//CHFS/Shared Documents/OpenData/datasets/staging/all_patrons_new.csv').st_size == 0:
            csv_writer.writeheader()
        
        for entry in checked_addresses:
            csv_writer.writerow(entry)

    # Writes CSV of rejected addresses
    with open("//CHFS/Shared Documents/OpenData/datasets/staging/bad_patron_addresses.csv", "w+") as bad_patrons:
        fieldnames_2 = skipped_addresses[0].keys()
        csv_writer = csv.DictWriter(bad_patrons, fieldnames=fieldnames_2, extrasaction='ignore', delimiter=',')
        
        if os.stat('//CHFS/Shared Documents/OpenData/datasets/staging/bad_patron_addresses.csv').st_size == 0:
            csv_writer.writeheader()
        
        for entry in skipped_addresses:
            csv_writer.writerow(entry)

# requests access token from Sierra each time it's called
def get_token():
    url = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/token"

    # Get the API key from secrets file
    header = {"Authorization": "Basic " + str(secrets.sierra_api), "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, headers=header)
    json_response = json.loads(response.text)
    # Create var to hold the response data
    active_patrons_token = json_response["access_token"]
    return active_patrons_token

# begin script
get_all_patrons()