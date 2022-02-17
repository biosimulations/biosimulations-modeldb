from Bio import Entrez
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import Config
from biosimulators_utils.omex_meta.data_model import BIOSIMULATIONS_ROOT_URI_FORMAT, OmexMetadataOutputFormat
from biosimulators_utils.omex_meta.io import BiosimulationsOmexMetaWriter, BiosimulationsOmexMetaReader
# from biosimulators_utils.omex_meta.utils import build_omex_meta_file_for_model
from biosimulators_utils.ref.data_model import Reference, JournalArticle, PubMedCentralOpenAccesGraphic  # noqa: F401
from biosimulators_utils.ref.utils import get_reference, get_pubmed_central_open_access_graphics
from biosimulators_utils.sedml.data_model import (
    SedDocument, Model, ModelLanguage, UniformTimeCourseSimulation,
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
import markdownify
import natsort
import os
import pkg_resources
import shutil
import tempfile
import time
import warnings
import yaml

Entrez.email = os.getenv('ENTREZ_EMAIL', None)

__all__ = ['import_models']

MODELING_APPLICATION = 'XPP'
CONCEPT_URI_PATTERN = 'http://modeldb.science/ModelList?id={}'
BIOSIMULATIONS_PROJECT_ID_PATTERN = 'modeldb-{}'
BIOSIMULATORS_SIMULATOR_ID = 'xpp'
ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY_PATTERN = os.path.join('article-figures', '{}')

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'modeldb-bqbiol-map.yml')), 'r') as file:
    MODELDB_BQBIOL_MAP = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'taxa.yml')), 'r') as file:
    TAXA = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'file-ext-format-uri-map.yml')), 'r') as file:
    FILE_EXTENSION_FORMAT_URI_MAP = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'set-file-map.yml')), 'r') as file:
    SET_FILE_MAP = yaml.load(file, Loader=yaml.Loader)


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


def get_metadata_for_model(model, model_dirname, config):
    """ Get additional metadata about a model

    * NCBI Taxonomy id of the organism
    * PubMed id, PubMed Central id and DOI for the reference
    * Open access figures for the reference

    Args:
        model (:obj:`dict`): information about a model
        model_dirname (:obj:`str`): path to the directory of files for the model
        config (:obj:`dict`): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`str`: description
            * :obj:`list` of :obj:`dict`: NCBI taxonomy identifiers and names
            * :obj:`list` of :obj:`dict`: structured information about the references
            * :obj:`list` of :obj:`PubMedCentralOpenAccesGraphic`: figures of the references
    """
    metadata_filename = os.path.join(config['final_metadata_dirname'], str(model['id']) + '.yml')

    # read from cache
    if os.path.isfile(metadata_filename):
        with open(metadata_filename, 'r') as file:
            metadata = yaml.load(file, Loader=yaml.Loader)
        description = metadata.get('description', None)
        taxa = metadata.get('taxa', [])
        references = metadata.get('references', [])
        thumbnails = metadata.get('thumbnails', [])

        for thumbnail in thumbnails:
            thumbnail['filename'] = os.path.join(config['source_thumbnails_dirname'], thumbnail['filename'])

        thumbnails = [PubMedCentralOpenAccesGraphic(**thumbnail) for thumbnail in thumbnails]

        return description, taxa, references, thumbnails

    # get description from readme
    description = None
    for rel_filename in os.listdir(model_dirname):
        basename, ext = os.path.splitext(rel_filename.lower())
        abs_filename = os.path.join(model_dirname, rel_filename)
        if basename == 'readme':
            if ext in ['', '.txt', '.md']:
                with open(abs_filename, 'r') as file:
                    description = file.read()

            elif ext in ['.html']:
                with open(abs_filename, 'rb') as file:
                    doc = bs4.BeautifulSoup(file.read())
                    description = markdownify.MarkdownConverter(strip=['img']).convert_soup(doc.find('body') or doc).strip()

            elif ext in ['.docx']:
                description = None  # TODO

            else:
                raise NotImplementedError('README type `{}` is not supported.'.format(ext))

            break

    # TODO: get images (png, jpg, JPG)

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

            # manually correct an invalid DOI
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
        'description': description,
        'taxa': taxa,
        'references': references,
        'thumbnails': [dataclasses.asdict(thumbnail) for thumbnail in thumbnails],
    }
    for thumbnail in metadata['thumbnails']:
        thumbnail['filename'] = os.path.relpath(thumbnail['filename'], config['source_thumbnails_dirname'])
    with open(metadata_filename, 'w') as file:
        file.write(yaml.dump(metadata))

    return (description, taxa, references, thumbnails)


def export_project_metadata_for_model_to_omex_metadata(model, description, taxa, references, thumbnails, metadata_filename, config):
    """ Export metadata about a model to an OMEX metadata RDF-XML file

    Args:
        model (:obj:`str`): information about the model
        description (:obj:`str`): description of the model
        taxa (:obj:`list` of :obj:`dict`): NCBI taxonomy identifier and name
        references (:obj:`list` of :obj:`dict`): structured information about the reference
        thumbnails (:obj:`list` of :obj:`PubMedCentralOpenAccesGraphic`): figures of the reference
        metadata_filename (:obj:`str`): path to save metadata
        config (:obj:`dict`): configuration
    """
    encodes = []
    for attr in MODELDB_BQBIOL_MAP:
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
        'description': description,
        'taxa': taxa,
        'encodes': encodes,
        'thumbnails': [
            os.path.join(
                ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY_PATTERN.format(os.path.basename(os.path.dirname(thumbnail.filename))),
                os.path.basename(thumbnail.filename),
            )
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


def build_combine_archive_for_model(id, model_dirname, archive_filename, extra_contents):
    """ Build a COMBINE/OMEX archive for a model including a SED-ML file

    Args:
        id (:obj:`str`): model id
        model_dirname (:obj:`str`): path to the directory of files for the model
        archive_filename (:obj:`str`): path to save the COMBINE/OMEX archive
        extra_contents (:obj:`dict`): dictionary that maps the local path of each additional file that
            should be included in the arrchive to its intended location within the archive and format
    """
    # make temporary directory for archive
    archive_dirname = tempfile.mkdtemp()
    shutil.rmtree(archive_dirname)
    archive = CombineArchive()

    # add files from ModelDB
    shutil.copytree(model_dirname, archive_dirname)
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
            uri = FILE_EXTENSION_FORMAT_URI_MAP.get(ext.lower(), None)
            if uri is None:
                uri = CombineArchiveContentFormat.OTHER
                msg = 'URI for `{}` for model `{}` is not known'.format(location, id)
                warnings.warn(msg, UserWarning)

        archive.contents.append(CombineArchiveContent(
            location=location,
            format=uri,
        ))

    # create simulations
    model_filenames = natsort.natsorted(
        glob.glob(os.path.join(model_dirname, '*.ode'))
        + glob.glob(os.path.join(model_dirname, '*.ODE'))
        + glob.glob(os.path.join(model_dirname, '*.xpp'))
        + glob.glob(os.path.join(model_dirname, '*.XPP'))
    )

    for model_filename in model_filenames:
        model_location = os.path.relpath(model_filename, model_dirname)

        sed_doc = SedDocument()

        # base model
        sed_base_model = Model(
            id='model',
            name='Model',
            source=os.path.basename(model_filename),
            language=ModelLanguage.XPP.value,
        )
        sed_doc.models.append(sed_base_model)

        # model variants
        set_files = SET_FILE_MAP.get(str(id), {}).get(model_location, [])
        if set_files:
            for set_file in set_files:
                set_file['filename'] = os.path.join(model_dirname, set_file['filename'])
        else:
            set_files = [{
                'filename': None,
                'id': None,
                'name': None,
            }]

        for set_file in set_files:
            sed_params, sed_sims, sed_vars, _ = get_parameters_variables_outputs_for_simulation(
                model_filename, ModelLanguage.XPP, UniformTimeCourseSimulation, native_ids=True,
                model_language_options={
                    'set_filename': set_file['filename'],
                })

            # model
            if set_file['id']:
                sed_model = Model(
                    id='model_' + set_file['id'],
                    name=set_file['name'],
                    source='#' + sed_base_model.id,
                    language=ModelLanguage.XPP.value,
                    changes=sed_params,
                )
                sed_doc.models.append(sed_model)
            else:
                sed_model = sed_base_model

            # simulation
            sed_sim = sed_sims[0]
            sed_sim.id = 'simulation'
            if set_file['id']:
                sed_sim.id += '_' + set_file['id']
            sed_sim.name = set_file['name'] or 'Simulation'
            sed_doc.simulations.append(sed_sim)

            # task
            sed_task = Task(
                id='task',
                name=set_file['name'] or 'Task',
                model=sed_model,
                simulation=sed_sim,
            )
            if set_file['id']:
                sed_task.id += '_' + set_file['id']
            sed_doc.tasks.append(sed_task)

            # data generators and report
            sed_report = Report(
                id='report',
                name=set_file['name'] or 'Report',
            )
            if set_file['id']:
                sed_report.id += '_' + set_file['id']

            sed_doc.outputs.append(sed_report)

            for sed_var in sed_vars:
                var_id = sed_var.id or 'T'

                sed_var.id = 'variable_' + var_id
                if set_file['id']:
                    sed_var.id += '_' + set_file['id']
                sed_var.name = var_id
                sed_var.task = sed_task

                sed_data_gen = DataGenerator(
                    id='data_generator_{}'.format(var_id),
                    name=var_id,
                    variables=[sed_var],
                    math=sed_var.id,
                )
                if set_file['id']:
                    sed_data_gen.id += '_' + set_file['id']
                sed_doc.data_generators.append(sed_data_gen)

                sed_data_set = DataSet(
                    id='data_set_{}'.format(var_id),
                    name=var_id,
                    label=var_id,
                    data_generator=sed_data_gen,
                )
                if set_file['id']:
                    sed_data_set.id += '_' + set_file['id']
                sed_report.data_sets.append(sed_data_set)

            # TODO: plots

        sim_location = os.path.splitext(model_location)[0] + '.sedml'
        SedmlSimulationWriter().run(sed_doc, os.path.join(archive_dirname, sim_location))
        archive.contents.append(CombineArchiveContent(
            location=sim_location,
            format=CombineArchiveContentFormat.SED_ML.value,
            master=True,
        ))

    # add metadata and thumbnails
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
    model_ids = get_model_ids(config, MODELING_APPLICATION)

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

    # filter out models that don't have XPP files
    for model in list(models):
        model_dirname = os.path.join(config['source_models_dirname'], str(model['id']))
        if (
            not glob.glob(os.path.join(model_dirname, '**', '*.ode'), recursive=True)
            and not glob.glob(os.path.join(model_dirname, '**', '*.ODE'), recursive=True)
            and not glob.glob(os.path.join(model_dirname, '**', '*.xpp'), recursive=True)
            and not glob.glob(os.path.join(model_dirname, '**', '*.XPP'), recursive=True)
        ):
            models.remove(model)

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
        description, taxa, references, thumbnails = get_metadata_for_model(model, model_dirname, config)

        # export metadata to RDF
        print('Exporting project metadata for {} of {}: {}'.format(i_model + 1, len(models), str(model['id'])))
        project_metadata_filename = os.path.join(config['final_metadata_dirname'], str(model['id']) + '.rdf')
        if not os.path.isfile(project_metadata_filename) or config['update_combine_archives']:
            export_project_metadata_for_model_to_omex_metadata(model, description, taxa, references, thumbnails,
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
                    location=os.path.join(
                        ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY_PATTERN.format(os.path.basename(os.path.dirname(thumbnail.filename))),
                        os.path.basename(thumbnail.filename)),
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
            run_name = model['name']
            if config['publish_models']:
                project_id = BIOSIMULATIONS_PROJECT_ID_PATTERN.format(model['id'])
            else:
                project_id = None

            project_bucket_key = '{}.omex'.format(str(model['id']))
            bucket.upload_file(project_filename, project_bucket_key)
            project_url = '{}/{}/{}'.format(config['bucket_endpoint'], config['bucket_name'], project_bucket_key)

            runbiosimulations_id = biosimulators_utils.biosimulations.utils.run_simulation_project(
                run_name, project_url, BIOSIMULATORS_SIMULATOR_ID, project_id=project_id, purpose='academic', auth=auth)
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
