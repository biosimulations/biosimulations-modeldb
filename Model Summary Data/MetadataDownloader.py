import json,urllib.request
import requests
import json

response = requests.get('http://modeldb.science/api/v1/models?modeling_application=XPP')
response.raise_for_status()
model_ids = response.json()

for model_id in model_ids:
    data = urllib.request.urlopen("http://modeldb.science/api/v1/models/" + str(model_id)).read()
    output = json.loads(data)

    with open(str(model_id), "w") as outfile:
        json.dump(output, outfile)
