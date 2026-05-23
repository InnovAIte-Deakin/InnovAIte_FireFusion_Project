import urllib.request
import json

# URL of the dataset
url_1 = 'https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=a927e847-5818-43e2-8fe6-ad7e469fabd1&limit=1000'  
url_2 = 'https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=39f89a56-af38-49cf-98d3-26eca92c4466&limit=1000'

fileobj_1 = urllib.request.urlopen(url_1)
fileobj_2 = urllib.request.urlopen(url_2)

# Convert the response to a string and then to a JSON object
data_1 = json.load(fileobj_1)
data_2 = json.load(fileobj_2)

# Combine the two datasets into one
data = data_1
data['result']['records'].extend(data_2['result']['records'])

# Extract the relevant data from the JSON object
records = data['result']['records']

# Ensure merged records have continuous _id values.
for i, record in enumerate(records, start=1):
    record['_id'] = i

# Save the data to a json file
with open('bushfire_at_risk_register.json', 'w') as f:
    json.dump(records, f)

# Print the 1200th record to verify the data
# print(records[1199])
