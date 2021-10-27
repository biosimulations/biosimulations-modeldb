# pip install requests python_dateutil pyyaml

import dateutil.parser
import requests
import yaml
from collections import OrderedDict

# get list of models
response = requests.get('http://modeldb.science/api/v1/models?modeling_application=XPP')
response.raise_for_status()
model_ids = response.json()

# get models
for model_id in model_ids:
    # get model
    response = requests.get('http://modeldb.science/api/v1/models/' + str(model_id))
    response.raise_for_status()
    model = response.json() #expecting to get data in JSON (returns dictionary)



    
    name = "Model " + str(model['id'])
    
    title = model['name'] 
    
    abstract = model['notes']['value']
    
    curators = [{"Orcid": "0000-0002-0962-961X", "Name": "Briman Yang"}, {"Orcid": "0000-0002-2605-5080", "Name":"Jonathan Karr"}]

    keyword = []
    
    keyword_list = model['model_concept']['value']
    for keywords in keyword_list:
        keyword.append(keywords['object_name'])

    #taxon_id = model['neurons']['value'][0]['object_id'] 
    #taxon_response = requests.get('http://modeldb.science/api/v1/celltypes/' + str(taxon_id))
    #taxon_response.raise_for_status()
    #taxon_response_model = taxon_response.json()
    #taxon = taxon_response_model['organism']['value'][0]['object_name']
    
    paper_id = model['model_paper']['value'][0]['object_id']
    citation_response = requests.get('http://modeldb.science/api/v1/papers/' + str(paper_id))
    citation_response.raise_for_status()
    citation_response_model = citation_response.json()
       
    author_number = len(citation_response_model['authors']['value'])
    author_list = citation_response_model['authors']['value']
    
    author_names = []
    for authors in author_list:
        author_names.append(authors['object_name'] + ",")

    #authors = ' '.join([str(item) for item in author_names])    
    #citation_title = citation_response_model['title']['value']
    #citation_journal = citation_response_model['journal']['value']
    #citation_volume = citation_response_model['volume']['value']
    #citation_pages_start = citation_response_model['first_page']['value']
    #citation_pages_end = citation_response_model['last_page']['value']
    #citation_year = citation_response_model['year']['value']
    #citation_url = citation_response_model['url']['value']


    #citation = authors + ". " + citation_title + " " + citation_journal + " " #+ #citation_volume + ", " #+ citation_pages_start + "-" #+ citation_pages_end + " (" + citation_year + ") " #+ citation_url  

    #value = yaml.safe_load(model_paper['value'])
    #paper_object_id = yaml.safe_load(value['object_id'])
    license = ["spdxID: MIT"] 

    created = dateutil.parser.parse(model['created'])
    modified = dateutil.parser.parse(model['ver_date'])
    created_date = ['{}-{}-{}'.format(created.year, created.month, created.day)]
    modified_date = '{}-{}-{}'.format(modified.year, modified.month, modified.day)


    # export metadata
    metadata = {
      'Title': title,
      'Abstract': abstract, 
      #'thumbnails':
      'Keywords': keyword,
      #'Taxon': taxon, 
      'Authors': author_names, 
      'Curators': curators,
      #'Citations': citation, 
      'License': license,
      'Created': created_date,
      'Modified':modified_date,
    }

    md = OrderedDict(metadata)


    metadata_filename = str(model_id) + '.yml'
    with open(metadata_filename, 'w') as file:
        file.write(yaml.dump(md))

