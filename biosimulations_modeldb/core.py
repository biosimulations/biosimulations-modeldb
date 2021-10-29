# pip install requests python_dateutil pyyaml

import dateutil.parser
import requests
import yaml
from collections import OrderedDict

# get list of models
response = requests.get('http://modeldb.science/api/v1/models?modeling_application=XPP')
response.raise_for_status()
model_ids = response.json()

#model ids
#[35358, 45513, 57910, 58172, 58195, 58199, 58581, 62268, 62272, 62287, 62661, 62676, 64171, 64285, 66268, 76879, 79238, 83319, 83558, 83570, 83575, 84606, 87762, 97743, 97747, 97850, 105528, 111877, 112079, 112547, 112836, 112968, 114108, 114424, 114450, 114451, 114452, 116123, 116386, 116867, 117330, 118014, 120243, 120246, 125154, 125529, 125683, 125733, 127022, 127355, 136097, 136773, 137263, 140788, 142630, 142993, 143072, 143253, 145800, 145801, 146734, 147748, 148637, 149162, 150217, 151677, 152028, 152113, 152292, 152966, 167714, 167715, 182758, 185334, 187213, 187599, 189088, 189344, 190261, 206364, 206365, 206380, 222715, 227577, 228337, 229640, 235377, 235774, 239039, 240364, 240961, 247694, 247704, 249405, 255569, 256627, 257608, 258234, 259786, 260190, 260730, 264591, 266726]

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
    

    keyword_list = model.get('model_concept',"")
    if keyword != "":
        try: 
            keyword_list = model.get('model_concept',"").get('value',"")
        except AttributeError:
            pass
    for keywords in keyword_list:
        keyword.append(keywords['object_name'])

    #taxon_id = model['neurons']['value'][0]['object_id'] 
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
    authors = ' '.join([str(item) for item in author_names])

    citation_title = citation_response_model.get('title').get('value','')

    citation_journal = citation_response_model.get('journal', "")
    if type(citation_journal) != None:
        citation_journal = citation_response_model.get('journal').get('value',"")

    citation_volume = citation_response_model.get('volume', "")
    if citation_volume != "":
        citation_volume = citation_response_model.get('volume').get('value',"")

    citation_pages_start = citation_response_model.get('first_page',"")
    if citation_pages_start != "":
        citation_pages_start = citation_response_model.get('first_page').get('value',"")

    citation_pages_end = citation_response_model.get('last_page',"")
    if citation_pages_end != "":
        citation_pages_end = citation_response_model.get('last_page').get('value',"")
    citation_year = citation_response_model.get('year',"")
    if citation_year != "":
        citation_year = citation_response_model.get('year').get('value',"")
    citation_url = citation_response_model.get('url', "")
    if citation_url != "":
        citation_url = citation_response_model.get('url',"").get('value', "")
        
    citation = authors + ". " + citation_title + " " + citation_journal + " " + citation_volume + ", " + citation_pages_start + "-" + citation_pages_end + " (" + citation_year + ") " #+ citation_url  

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
      'Citations': citation, 
      'License': license,
      'Created': created_date,
      'Modified':modified_date,
    }

    md = OrderedDict(metadata)

    metadata_filename = str(model_id) + '.yml'
    with open(metadata_filename, 'w') as file:
        file.write(yaml.dump(metadata, default_flow_style=False))
        file.write(yaml.dump(md, default_flow_style=False))
print("Success")
