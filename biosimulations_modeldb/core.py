from Bio import Entrez
from biosimulators_utils.biosimulations.utils import get_file_extension_combine_uri_map as base_get_file_extension_combine_uri_map
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import Config
from biosimulators_utils.omex_meta.data_model import BIOSIMULATIONS_ROOT_URI_FORMAT, OmexMetadataOutputFormat
from biosimulators_utils.omex_meta.io import BiosimulationsOmexMetaWriter, BiosimulationsOmexMetaReader
# from biosimulators_utils.omex_meta.utils import build_omex_meta_file_for_model
from biosimulators_utils.ref.data_model import Reference, JournalArticle, PubMedCentralOpenAccesGraphic  # noqa: F401
from biosimulators_utils.ref.utils import get_reference, get_pubmed_central_open_access_graphics
from biosimulators_utils.sedml.data_model import (
    SedDocument, Model, ModelLanguage, SteadyStateSimulation,
    Task, DataGenerator, Report, DataSet)
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml.model_utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from biosimulators_utils.warnings import BioSimulatorsWarning
import biosimulators_xpp
import biosimulators_utils.biosimulations.utils
import boto3
import copy
import dataclasses
import datetime
import dateutil.parser
import git
import glob
import lxml.etree
import os
import shutil
import tempfile
import time
import warnings
import yaml

Entrez.email = os.getenv('ENTREZ_EMAIL', None)

__all__ = ['import_models']

CONCEPT_URI_PATTERN = 'http://modeldb.science/ModelList?id={}'

ENCODES_ATTRIBUTES = [
    {
        'attribute': 'model_type',
        'label': 'model type',
        'hasUri': True,
    },
    {
        'attribute': 'other_type',
        'label': 'model type',
        'hasUri': False,
    },
    {
        'attribute': 'region',
        'label': 'brain region',
        'hasUri': True,
    },
    {
        'attribute': 'neurons',
        'label': 'neuron',
        'hasUri': True,
    },
    {
        'attribute': 'other_neurons',
        'label': 'neuron',
        'hasUri': False,
    },
    {
        'attribute': 'currents',
        'label': 'ionic current',
        'hasUri': True,
    },
    {
        'attribute': 'other_currents',
        'label': 'ionic current',
        'hasUri': False,
    },
    {
        'attribute': 'neurotransmitters',
        'label': 'neurotransmitter',
        'hasUri': True,
    },
    {
        'attribute': 'other_neurotransmitter',
        'label': 'neurotransmitter',
        'hasUri': False,
    },
    {
        'attribute': 'receptors',
        'label': 'receptor',
        'hasUri': True,
    },
    {
        'attribute': 'other_receptors',
        'label': 'receptor',
        'hasUri': False,
    },
    {
        'attribute': 'gene',
        'label': 'gene',
        'hasUri': True,
    },
    {
        'attribute': 'model_concept',
        'label': 'model concept',
        'hasUri': True,
    },
    {
        'attribute': 'other_concept',
        'label': 'model concept',
        'hasUri': False,
    },
]

TAXA = {
    'Aplysia': {
        'label': 'Aplysia',
        'uri': 'http://identifiers.org/taxonomy:6499',
    },
    'Drosophila': {
        'label': 'Drosophila',
        'uri': 'http://identifiers.org/taxonomy:7215',
    },
    'Drosophila (fruit fly)': {
        'label': 'Drosophila',
        'uri': 'http://identifiers.org/taxonomy:7215',
    },
    'Helix pomatia (snail)': {
        'label': 'Helix pomatia',
        'uri': 'http://identifiers.org/taxonomy:6536',
    },
}


def get_model_ids(config, modeling_application):
    """ Get a list of the ids of models in the source database for a particular modeling application (e.g., XPP)

    Args:
        config (:obj:`dict`): configuration
        modeling_application (:obj:`str`): modeling application (e.g., ``XPP``)

    Returns:
        :obj:`list` of :obj:`int`: ids of models
    """
    response = config['source_session'].get(config['source_api_endpoint'] + '/models?modeling_application={}'.format(modeling_application))
    response.raise_for_status()
    models = response.json()
    models.sort()
    return models


def get_model(id, config):
    """ Get the details of a model from the source database and download the associated files

    Args:
        id (:obj:`int`): id of the model
        config (:obj:`dict`): configuration

    Returns:
        :obj:`dict`: detailed information about the model
    """
    # get information about the model
    response = config['source_session'].get(config['source_api_endpoint'] + '/models/' + str(id))
    response.raise_for_status()
    model = response.json()

    # get information about the papers
    for paper in model['model_paper']['value']:
        response = config['source_session'].get(config['source_api_endpoint'] + '/papers/' + str(paper['object_id']))
        response.raise_for_status()
        paper_details = response.json()

        if 'fist_page' in paper_details:
            pages = paper_details['fist_page']['value']
            if 'last_page' in paper_details:
                pages += '-' + paper_details['last_page']['value']
        else:
            pages = None

        article = JournalArticle(
            authors=[author['object_name'] for author in paper_details['authors']['value']],
            title=paper_details['title']['value'],
            journal=paper_details['journal']['value'],
            volume=paper_details.get('volume', {}).get('value', None),
            issue=None,
            pages=pages,
            year=int(paper_details['year']['value']),
        )

        paper['uris'] = {
            'doi': paper_details.get('doi', {}).get('value', None),
            'pubmed': paper_details.get('pubmed_id', {}).get('value', None),
            'url': paper_details.get('url', {}).get('value', None),
        }
        paper['citation'] = article

    # download the files for the model by adding it as a submodule
    model_dirname = os.path.join(config['source_models_dirname'], str(id))
    if not os.path.isdir(model_dirname):
        model_repo_url = '{}/{}.git'.format(config['source_models_git_repository_organization'], id)
        repo = git.Repo(config['source_repository'])
        git.Submodule.add(repo, str(id), model_dirname, model_repo_url)

    # return the details of the model
    return model


def get_metadata_for_model(model, config):
    """ Get additional metadata about a model

    * NCBI Taxonomy id of the organism
    * PubMed id, PubMed Central id and DOI for the reference
    * Open access figures for the reference

    Args:
        model (:obj:`dict`): information about a model
        config (:obj:`dict`): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`list` of :obj:`dict`: NCBI taxonomy identifiers and names
            * :obj:`list` of :obj:`dict`: structured information about the references
            * :obj:`list` of :obj:`PubMedCentralOpenAccesGraphic`: figures of the references
    """
    metadata_filename = os.path.join(config['final_metadata_dirname'], str(model['id']) + '.yml')

    # read from cache
    if os.path.isfile(metadata_filename):
        with open(metadata_filename, 'r') as file:
            metadata = yaml.load(file, Loader=yaml.Loader)
        taxa = metadata.get('taxa', [])
        references = metadata.get('references', [])
        thumbnails = metadata.get('thumbnails', [])

        thumbnails = [PubMedCentralOpenAccesGraphic(**thumbnail) for thumbnail in thumbnails]

        return taxa, references, thumbnails

    # get taxa
    taxa_ids = set()
    taxa = []
    for species in model.get('species', {}).get('value', []):
        taxon = TAXA.get(species['object_name'], None)
        if not taxon:
            raise ValueError("Taxonomy must be annotated for species '{}'".format(species['object_name']))
        taxa_ids.add(taxon['uri'])
        taxa.append(taxon)

    for region in model.get('region', {}).get('value', []):
        taxon = TAXA.get(region['object_name'], None)
        if taxon and taxon['uri'] not in taxa_ids:
            taxa_ids.add(taxon['uri'])
            taxa.append(taxon)

    # get citations and figures
    references = []
    thumbnails = []
    for paper in model.get('model_paper', {}).get('value', []):
        if paper['uris']['doi'] or paper['uris']['pubmed']:
            time.sleep(config['entrez_delay'])

            article = get_reference(
                paper['uris']['pubmed'],
                paper['uris']['doi'],
                cross_ref_session=config['cross_ref_session'],
            )

            if paper['object_id'] == 39981:
                article.doi = '10.1523/JNEUROSCI.22-07-02963.2002'

            if article.doi:
                uri = 'http://identifiers.org/doi:{}'.format(article.doi)
            else:
                uri = 'http://identifiers.org/pubmed:{}'.format(article.pubmed_id)

            # Figures for the associated publication from open-access subset of PubMed Central
            if article.pubmed_central_id:
                thumbnails.extend(get_pubmed_central_open_access_graphics(
                    article.pubmed_central_id,
                    os.path.join(config['source_thumbnails_dirname'], article.pubmed_central_id),
                    session=config['pubmed_central_open_access_session'],
                ))

        else:
            uri = paper['uris']['url']
            article = paper['citation']

        references.append({
            'uri': uri,
            'label': article.get_citation(),
        })

    # save metadata
    metadata = {
        'taxa': taxa,
        'references': references,
        'thumbnails': [dataclasses.asdict(thumbnail) for thumbnail in thumbnails],
    }
    with open(metadata_filename, 'w') as file:
        file.write(yaml.dump(metadata))

    return (taxa, references, thumbnails)


def export_project_metadata_for_model_to_omex_metadata(model, taxa, references, thumbnails, metadata_filename, config):
    """ Export metadata about a model to an OMEX metadata RDF-XML file

    Args:
        model (:obj:`str`): information about the model
        taxa (:obj:`list` of :obj:`dict`): NCBI taxonomy identifier and name
        references (:obj:`list` of :obj:`dict`): structured information about the reference
        thumbnails (:obj:`list` of :obj:`PubMedCentralOpenAccesGraphic`): figures of the reference
        metadata_filename (:obj:`str`): path to save metadata
        config (:obj:`dict`): configuration
    """
    encodes = []
    for attr in ENCODES_ATTRIBUTES:
        if attr['hasUri']:
            for object in model.get(attr['attribute'], {}).get('value', []):
                object_name = object['object_name']
                if attr['attribute'] == 'region':
                    if object_name in ['Generic', 'Uknown'] or object_name in TAXA:
                        continue

                    object_name = object_name.partition(' (')[0]

                encodes.append({
                    'uri': 'http://modeldb.science/ModelList?id={}'.format(object['object_id']),
                    'label': object_name,
                })
        else:
            object_name = model.get(attr['attribute'], {}).get('value', None)
            if object_name:
                encodes.append({
                    'label': object_name,
                })

    creators = []
    for implemented_by in model.get('implemented_by', {}).get('value', []):
        name, _, email = implemented_by['object_name'].partition(' [')
        last_name, _, first_name = name.partition(', ')
        if email:
            user, _, domain = email.partition(' at ')
            uri = 'mailto:{}@{}'.format(user, domain[0:-1])
        else:
            uri = None
        creators.append({
            'label': '{} {}'.format(first_name, last_name).strip(),
            'uri': uri,
        })

    contributors = copy.deepcopy(config['curators'])
    if model.get('public_submitter_name', None):
        submitter = {
            'label': model['public_submitter_name']['value'],
            'uri': None,
        }
        if model.get('public_submitter_email', None):
            submitter['uri'] = 'mailto:' + model['public_submitter_email']['value']
        contributors.insert(0, submitter)

    created = dateutil.parser.parse(model['created'])
    last_updated = dateutil.parser.parse(model['ver_date'])

    metadata = {
        "uri": '.',
        "combine_archive_uri": BIOSIMULATIONS_ROOT_URI_FORMAT.format(model['id']),
        'title': model['name'],
        'abstract': model.get('notes', {}).get('value', None),
        'keywords': [
        ],
        'description': None,
        'taxa': taxa,
        'encodes': encodes,
        'thumbnails': [
            os.path.join('article-figures', os.path.basename(os.path.dirname(thumbnail.filename)), os.path.basename(thumbnail.filename))
            for thumbnail in thumbnails
        ],
        'sources': [],
        'predecessors': [],
        'successors': [],
        'see_also': [],
        'creators': creators,
        'contributors': contributors,
        'identifiers': [
            {
                'uri': 'https://identifiers.org/modeldb:{}'.format(model['id']),
                'label': 'modeldb:{}'.format(model['id']),
            },
        ],
        'citations': references,
        'license': None,
        'funders': [],
        'created': '{}-{:02d}-{:02d}'.format(created.year, created.month, created.day),
        'modified': [
            '{}-{:02d}-{:02d}'.format(last_updated.year, last_updated.month, last_updated.day),
        ],
        'other': [],
    }
    writer_config = Config(OMEX_METADATA_OUTPUT_FORMAT=OmexMetadataOutputFormat.rdfxml)
    BiosimulationsOmexMetaWriter().run([metadata], metadata_filename, config=writer_config)
    _, errors, warnings = BiosimulationsOmexMetaReader().run(metadata_filename)
    if errors:
        raise ValueError('The metadata is not valid:\n  {}'.format(flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))


file_extension_combine_uri_map = None


def get_file_extension_combine_uri_map():
    """ Get a map from file extensions to URIs for use with manifests of COMBINE/OMEX archives

    Args:
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`dict`: which maps extensions to lists of associated URIs
    """
    global file_extension_combine_uri_map
    if file_extension_combine_uri_map is None:
        file_extension_combine_uri_map = base_get_file_extension_combine_uri_map()
        file_extension_combine_uri_map['ac'] = {'http://purl.org/NET/mediatypes/text/x-autoconf'}
        file_extension_combine_uri_map['auto'] = {CombineArchiveContentFormat.XPP_AUTO}
        file_extension_combine_uri_map['cc'] = file_extension_combine_uri_map['cpp']
        file_extension_combine_uri_map['dist'] = {CombineArchiveContentFormat.MARKDOWN}
        file_extension_combine_uri_map['eps'] = {CombineArchiveContentFormat.POSTSCRIPT}
        file_extension_combine_uri_map['fig'] = {CombineArchiveContentFormat.MATLAB_FIGURE}
        file_extension_combine_uri_map['g'] = {CombineArchiveContentFormat.GENESIS}
        file_extension_combine_uri_map['hoc'] = {CombineArchiveContentFormat.HOC}
        file_extension_combine_uri_map['html'] = {CombineArchiveContentFormat.HTML}
        file_extension_combine_uri_map['in'] = {CombineArchiveContentFormat.NCS}
        file_extension_combine_uri_map['inc'] = {CombineArchiveContentFormat.NMODL}
        file_extension_combine_uri_map['map'] = {CombineArchiveContentFormat.TSV}
        file_extension_combine_uri_map['md'] = {CombineArchiveContentFormat.MARKDOWN}
        file_extension_combine_uri_map['mlx'] = {'http://purl.org/NET/mediatypes/application/matlab-live-script'}
        file_extension_combine_uri_map['mod'] = {CombineArchiveContentFormat.NMODL}
        file_extension_combine_uri_map['mw'] = {CombineArchiveContentFormat.MAPLE_WORKSHEET}
        file_extension_combine_uri_map['nb'] = {CombineArchiveContentFormat.MATHEMATICA_NOTEBOOK}
        file_extension_combine_uri_map['nrn'] = {CombineArchiveContentFormat.HOC}
        file_extension_combine_uri_map['ode'] = {CombineArchiveContentFormat.XPP}
        file_extension_combine_uri_map['p'] = {CombineArchiveContentFormat.GENESIS}
        file_extension_combine_uri_map['ps'] = {CombineArchiveContentFormat.POSTSCRIPT}
        file_extension_combine_uri_map['sce'] = {CombineArchiveContentFormat.Scilab}
        file_extension_combine_uri_map['ses'] = {CombineArchiveContentFormat.NEURON_SESSION}
        file_extension_combine_uri_map['set'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['sfit'] = {CombineArchiveContentFormat.MATLAB_DATA}
        file_extension_combine_uri_map['sli'] = {CombineArchiveContentFormat.SLI}
        file_extension_combine_uri_map['tab'] = {CombineArchiveContentFormat.TSV}
        file_extension_combine_uri_map['txt'] = {CombineArchiveContentFormat.TEXT}
        file_extension_combine_uri_map['xls'] = {CombineArchiveContentFormat.XLS}
        file_extension_combine_uri_map['xpp'] = {CombineArchiveContentFormat.XPP}

        file_extension_combine_uri_map['inp'] = {CombineArchiveContentFormat.TEXT}

        file_extension_combine_uri_map[''] = {CombineArchiveContentFormat.OTHER}
        file_extension_combine_uri_map['bin'] = {CombineArchiveContentFormat.OTHER}
        file_extension_combine_uri_map['dat'] = {CombineArchiveContentFormat.OTHER}
        file_extension_combine_uri_map['mexmaci64'] = {CombineArchiveContentFormat.OTHER}
        file_extension_combine_uri_map['mexw64'] = {CombineArchiveContentFormat.OTHER}
        file_extension_combine_uri_map['mexa64'] = {CombineArchiveContentFormat.OTHER}

        file_extension_combine_uri_map['set3'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['setdb'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['setnorm'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['setpark'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['setsb'] = {CombineArchiveContentFormat.XPP_SET}
        file_extension_combine_uri_map['setsdb'] = {CombineArchiveContentFormat.XPP_SET}
    return file_extension_combine_uri_map


def build_combine_archive_for_model(id, model_dirname, archive_filename, extra_contents):
    """ Build a COMBINE/OMEX archive for a model including a SED-ML file

    Args:
        id (:obj:`str`): model id
        model_dirname (:obj:`str`): path to the directory of files for the model
        archive_filename (:obj:`str`): path to save the COMBINE/OMEX archive
        extra_contents (:obj:`dict`): dictionary that maps the local path of each additional file that
            should be included in the arrchive to its intended location within the archive and format
    """

    params, sims, vars, outputs = get_parameters_variables_outputs_for_simulation(
        model_filename, ModelLanguage.SBML, SteadyStateSimulation, native_ids=True)

    obj_vars = list(filter(lambda var: var.target.startswith('/sbml:sbml/sbml:model/fbc:listOfObjectives/'), vars))
    rxn_flux_vars = list(filter(lambda var: var.target.startswith('/sbml:sbml/sbml:model/sbml:listOfReactions/'), vars))

    sedml_doc = SedDocument()
    model = Model(
        id='model',
        source=os.path.basename(model_filename),
        language=ModelLanguage.SBML.value,
        changes=params,
    )
    sedml_doc.models.append(model)
    sim = sims[0]
    sedml_doc.simulations.append(sim)

    task = Task(
        id='task',
        model=model,
        simulation=sim,
    )
    sedml_doc.tasks.append(task)

    report = Report(
        id='objective',
        name='Objective',
    )
    sedml_doc.outputs.append(report)
    for var in obj_vars:
        var_id = var.id
        var_name = var.name

        var.id = 'variable_' + var_id
        var.name = None

        var.task = task
        data_gen = DataGenerator(
            id='data_generator_{}'.format(var_id),
            variables=[var],
            math=var.id,
        )
        sedml_doc.data_generators.append(data_gen)
        report.data_sets.append(DataSet(
            id=var_id,
            label=var_id,
            name=var_name,
            data_generator=data_gen,
        ))

    report = Report(
        id='reaction_fluxes',
        name='Reaction fluxes',
    )
    sedml_doc.outputs.append(report)
    for var in rxn_flux_vars:
        var_id = var.id
        var_name = var.name

        var.id = 'variable_' + var_id
        var.name = None

        var.task = task
        data_gen = DataGenerator(
            id='data_generator_{}'.format(var_id),
            variables=[var],
            math=var.id,
        )
        sedml_doc.data_generators.append(data_gen)
        report.data_sets.append(DataSet(
            id=var_id,
            label=var_id[2:] if var_id.startswith('R_') else var_id,
            name=var_name if len(rxn_flux_vars) < 4000 else None,
            data_generator=data_gen,
        ))

    # make temporary directory for archive
    archive_dirname = tempfile.mkdtemp()
    shutil.rmtree(archive_dirname)
    archive = CombineArchive()

    shutil.copytree(model_dirname, archive_dirname)
    file_extension_combine_uri_map = get_file_extension_combine_uri_map()
    for filename in glob.glob(os.path.join(model_dirname, '**', '*'), recursive=True):
        location = os.path.relpath(filename, model_dirname)
        if os.path.isdir(filename):
            continue
        if location in ['.git', 'desktop.ini']:
            continue

        _, ext = os.path.splitext(location)
        if ext:
            ext = ext[1:]
        if ext == 'pyc':
            continue

        if ext == 'xml':
            doc = lxml.etree.parse(filename)
            ns = doc.getroot().nsmap[None]
            if ns.startswith('http://www.sbml.org/sbml/'):
                uri = CombineArchiveContentFormat.SBML
            elif ns.startswith('http://morphml.org/neuroml/schema'):
                uri = CombineArchiveContentFormat.NeuroML
            else:
                uri = CombineArchiveContentFormat.XML

        else:
            uris = list(file_extension_combine_uri_map.get(ext.lower(), set()))
            if len(uris) == 0:
                uri = CombineArchiveContentFormat.OTHER
                msg = 'URI for `{}` for model `{}` is not known'.format(location, id)
                warnings.warn(msg, UserWarning)
            elif len(uris) == 1:
                uri = uris[0]
            else:
                uri = uris[0]
                msg = 'URI for `{}` for model `{}` could not be uniquely determined:\n  {}'.format(
                    location, id, '\n  '.join(sorted(uris)))
                warnings.warn(msg, UserWarning)

        archive.contents.append(CombineArchiveContent(
            location=location,
            format=uri,
        ))

    SedmlSimulationWriter().run(sedml_doc, os.path.join(archive_dirname, 'simulation.sedml'))
    archive.contents.append(CombineArchiveContent(
        location='simulation.sedml',
        format=CombineArchiveContentFormat.SED_ML.value,
        master=True,
    ))

    for local_path, extra_content in extra_contents.items():
        extra_content_dirname = os.path.dirname(os.path.join(archive_dirname, extra_content.location))
        if not os.path.isdir(extra_content_dirname):
            os.makedirs(extra_content_dirname)
        shutil.copyfile(local_path, os.path.join(archive_dirname, extra_content.location))
        archive.contents.append(extra_content)

    # save archive to file
    CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

    # clean up temporary directory for archive
    shutil.rmtree(archive_dirname)


def import_models(config):
    """ Download the source database, convert into COMBINE/OMEX archives, simulate the archives, and submit them to BioSimulations

    Args:
        config (:obj:`dict`): configuration
    """

    # create directories for source files, thumbnails, projects, and simulation results
    if not os.path.isdir(config['source_models_dirname']):
        os.makedirs(config['source_models_dirname'])
    if not os.path.isdir(config['source_thumbnails_dirname']):
        os.makedirs(config['source_thumbnails_dirname'])

    if not os.path.isdir(config['final_visualizations_dirname']):
        os.makedirs(config['final_visualizations_dirname'])
    if not os.path.isdir(config['final_metadata_dirname']):
        os.makedirs(config['final_metadata_dirname'])
    if not os.path.isdir(config['final_projects_dirname']):
        os.makedirs(config['final_projects_dirname'])
    if not os.path.isdir(config['final_simulation_results_dirname']):
        os.makedirs(config['final_simulation_results_dirname'])

    # read import status file
    if os.path.isfile(config['status_filename']):
        with open(config['status_filename'], 'r') as file:
            status = yaml.load(file, Loader=yaml.Loader)
    else:
        status = {}

    # read import issues file
    with open(config['issues_filename'], 'r') as file:
        issues = yaml.load(file, Loader=yaml.Loader)

    # get a list of the ids of all models available in the source database
    model_ids = get_model_ids(config, 'XPP')

    # limit the number of models to import
    model_ids = model_ids[0:config['max_models']]

    # get the details of each model
    models = []
    update_times = {}
    for i_model, model_id in enumerate(model_ids):
        print('Retrieving {} of {}: {} ...'.format(i_model + 1, len(models), model_id))

        # update status
        update_times[model_id] = datetime.datetime.utcnow()

        # get the details of the model and download it from the source database
        model = get_model(model_id, config)
        models.append(model)

    # filter out models that don't need to be imported because they've already been imported and haven't been updated
    if not config['update_simulation_runs']:
        models = list(filter(
            lambda model:
            (
                str(model['id']) not in status
                or not status[str(model['id'])]['runbiosimulationsId']
                or (
                    (dateutil.parser.parse(model['last_updated']) + datetime.timedelta(1))
                    > dateutil.parser.parse(status[str(model['id'])]['updated'])
                )
            ),
            models
        ))

    # filter out models with issues
    models = list(filter(lambda model: str(model['id']) not in issues, models))

    # get S3 bucket to save archives
    s3 = boto3.resource('s3',
                        endpoint_url=config['bucket_endpoint'],
                        aws_access_key_id=config['bucket_access_key_id'],
                        aws_secret_access_key=config['bucket_secret_access_key'],
                        verify=False)
    bucket = s3.Bucket(config['bucket_name'])

    # get authorization for BioSimulations API
    auth = biosimulators_utils.biosimulations.utils.get_authorization_for_client(
        config['biosimulations_api_client_id'], config['biosimulations_api_client_secret'])

    # download models, convert them to COMBINE/OMEX archives, simulate them, and deposit them to the BioSimulations database
    for i_model, model in enumerate(models):
        model_dirname = os.path.join(config['source_models_dirname'], str(model['id']))

        # get additional metadata about the model
        print('Getting metadata for {} of {}: {}'.format(i_model + 1, len(models), str(model['id'])))
        taxa, references, thumbnails = get_metadata_for_model(model, config)

        # export metadata to RDF
        print('Exporting project metadata for {} of {}: {}'.format(i_model + 1, len(models), str(model['id'])))
        project_metadata_filename = os.path.join(config['final_metadata_dirname'], str(model['id']) + '.rdf')
        if not os.path.isfile(project_metadata_filename) or config['update_combine_archives']:
            export_project_metadata_for_model_to_omex_metadata(model, taxa, references, thumbnails,
                                                               project_metadata_filename, config)

        # package model into COMBINE/OMEX archive
        print('Converting model {} of {}: {} ...'.format(i_model + 1, len(models), str(model['id'])))
        project_filename = os.path.join(config['final_projects_dirname'], str(model['id']) + '.omex')
        if not os.path.isfile(project_filename) or config['update_combine_archives']:
            extra_contents = {}

            extra_contents[project_metadata_filename] = CombineArchiveContent(
                location='metadata.rdf',
                format=CombineArchiveContentFormat.OMEX_METADATA,
            )

            for thumbnail in thumbnails:
                extra_contents[thumbnail.filename] = CombineArchiveContent(
                    location=os.path.join('article-figures', os.path.basename(os.path.dirname(
                        thumbnail.filename)), os.path.basename(thumbnail.filename)),
                    format=CombineArchiveContentFormat.JPEG,
                )

            build_combine_archive_for_model(model['id'], model_dirname, project_filename, extra_contents=extra_contents)

        # simulate COMBINE/OMEX archives
        print('Simulating model {} of {}: {} ...'.format(i_model + 1, len(models), str(model['id'])))

        if config['simulate_models']:
            out_dirname = os.path.join(config['final_simulation_results_dirname'], str(model['id']))
            biosimulators_utils_config = Config(COLLECT_COMBINE_ARCHIVE_RESULTS=True)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", BioSimulatorsWarning)
                results, log = biosimulators_xpp.exec_sedml_docs_in_combine_archive(
                    project_filename, out_dirname, config=biosimulators_utils_config)
            if log.exception:
                print('Simulation of `{}` failed'.format(str(model['id'])))
                raise log.exception
            duration = log.duration
        else:
            duration = status.get(str(model['id']), {}).get('duration', None)

        # submit COMBINE/OMEX archive to BioSimulations
        if config['dry_run']:
            runbiosimulations_id = status.get(str(model['id']), {}).get('runbiosimulationsId', None)
            updated = status.get(str(model['id']), {}).get('updated', None)
        else:
            name = str(model['id'])
            if config['publish_models']:
                project_id = name
            else:
                project_id = None

            project_bucket_key = '{}{}.omex'.format(config['bucket_prefix'], str(model['id']))
            bucket.upload_file(project_filename, project_bucket_key, ExtraArgs={'ACL': 'public-read'})
            project_url = '{}{}'.format(config['bucket_public_endpoint'], project_bucket_key)

            runbiosimulations_id = biosimulators_utils.biosimulations.utils.run_simulation_project(
                name, project_url, 'xpp', project_id=project_id, purpose='academic', auth=auth)
            updated = str(update_times[str(model['id'])])

        # output status
        status[str(model['id'])] = {
            'created': status.get(str(model['id']), {}).get('created', str(update_times[str(model['id'])])),
            'updated': updated,
            'duration': duration,
            'runbiosimulationsId': runbiosimulations_id,
        }
        with open(config['status_filename'], 'w') as file:
            file.write(yaml.dump(status))
