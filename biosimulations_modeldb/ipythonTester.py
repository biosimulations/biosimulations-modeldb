
import dateutil.parser
import requests
import yaml
from collections import OrderedDict

# get list of models
response = requests.get('http://modeldb.science/api/v1/models?modeling_application=XPP')
response.raise_for_status()
model_ids = response.json()

response = requests.get('http://modeldb.science/api/v1/models/279')  
response.raise_for_status()
model = response.json()
paper_id = model['model_paper']['value'][0]['object_id']
citation_response = requests.get('http://modeldb.science/api/v1/papers/' + str(paper_id))
citation_response.raise_for_status()
citation_response_model = citation_response.json()