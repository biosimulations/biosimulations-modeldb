output_data = {
    'resources': [{
        'type': 'compute.v1.instance',
        'name': 'vm-created-by-deployment-manager',
        'properties': {
            'disks': [{
                'deviceName': '$disks_deviceName$',
                'boot': '$disks_boot$',
                'initializeParams': {
                    'sourceImage': '$disks_initializeParams_sourceImage$'
                },
                'autoDelete': '$disks_autoDelete$',
                'type': '$disks_type$'
            }],
            'machineType': '$machineType$',
            'zone': '$zone$',
            'networkInterfaces': [{
                'network': '$networkInterfaces_network$'
            }]
        }
    }]
}
import yaml
f = open('meta.yaml', 'w+')
yaml.dump(output_data, f, allow_unicode=True)

import dateutil.parser
import requests
import yaml
from collections import OrderedDict

# get list of models
response = requests.get('http://modeldb.science/api/v1/models?modeling_application=XPP')
response.raise_for_status()
model_ids = response.json()

print(model_ids)

[35358, 45513, 57910, 58172, 58195, 58199, 58581, 62268, 62272, 62287, 62661, 62676, 64171, 64285, 66268, 76879, 79238, 83319, 83558, 83570, 83575, 84606, 87762, 97743, 97747, 97850, 105528, 111877, 112079, 112547, 112836, 112968, 114108, 114424, 114450, 114451, 114452, 116123, 116386, 116867, 117330, 118014, 120243, 120246, 125154, 125529, 125683, 125733, 127022, 127355, 136097, 136773, 137263, 140788, 142630, 142993, 143072, 143253, 145800, 145801, 146734, 147748, 148637, 149162, 150217, 151677, 152028, 152113, 152292, 152966, 167714, 167715, 182758, 185334, 187213, 187599, 189088, 189344, 190261, 206364, 206365, 206380, 222715, 227577, 228337, 229640, 235377, 235774, 239039, 240364, 240961, 247694, 247704, 249405, 255569, 256627, 257608, 258234, 259786, 260190, 260730, 264591, 266726]
