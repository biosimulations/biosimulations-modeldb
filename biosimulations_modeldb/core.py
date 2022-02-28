from .utils import case_insensitive_glob, get_readme, get_images_for_project
from Bio import Entrez
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import Config
from biosimulators_utils.omex_meta.data_model import BIOSIMULATIONS_ROOT_URI_FORMAT, OmexMetadataOutputFormat
from biosimulators_utils.omex_meta.io import BiosimulationsOmexMetaWriter, BiosimulationsOmexMetaReader
# from biosimulators_utils.omex_meta.utils import build_omex_meta_file_for_model
from biosimulators_utils.ref.data_model import JournalArticle
from biosimulators_utils.ref.utils import get_reference, get_pubmed_central_open_access_graphics
from biosimulators_utils.sedml.data_model import (
    SedDocument, Model, ModelLanguage, UniformTimeCourseSimulation,
    Task, DataGenerator, Report, DataSet, Symbol)
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml.model_utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from biosimulators_utils.warnings import BioSimulatorsWarning
import biosimulators_xpp
import biosimulators_utils.biosimulations.utils
import boto3
import copy
import datetime
import dateutil.parser
import dotenv
import git
import glob
import imghdr
import lxml.etree
import natsort
import numpy
import os
import pkg_resources
import shutil
import sys
import time
import warnings
import yaml

env = {
    **dotenv.dotenv_values("config.env"),
    **os.environ,
}

Entrez.email = env.get('ENTREZ_EMAIL', None)

__all__ = ['import_projects']

MODELING_APPLICATION = 'XPP'
CONCEPT_URI_PATTERN = 'http://modeldb.science/ModelList?id={}'
BIOSIMULATIONS_PROJECT_ID_PATTERN = 'modeldb-{}'
BIOSIMULATORS_SIMULATOR_ID = 'xpp'
ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY = 'article-figures'

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'modeldb-bqbiol-map.yml')), 'r') as file:
    MODELDB_BQBIOL_MAP = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'taxa.yml')), 'r') as file:
    TAXA = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'file-ext-format-uri-map.yml')), 'r') as file:
    # file was built using ``biosimulations_modeldb.utils.get_file_extension_combine_uri_map``
    FILE_EXTENSION_FORMAT_URI_MAP = yaml.load(file, Loader=yaml.Loader)

with open(pkg_resources.resource_filename('biosimulations_modeldb', os.path.join('final', 'set-file-map.yml')), 'r') as file:
    SET_FILE_MAP = yaml.load(file, Loader=yaml.Loader)


def get_biosimulations_project_id(modeldb_id):
    """ Get the BioSimulations id for a project

    Args:
        modeldb_id (:obj:`str`): ModelDB id for the project

    Returns:
        :obj:`str`: BioSimulations id for the project
    """
    return BIOSIMULATIONS_PROJECT_ID_PATTERN.format(modeldb_id)


def get_project_ids(config, modeling_application):
    """ Get a list of the ids of models in the source database for a particular modeling application (e.g., XPP)

    Args:
        config (:obj:`dict`): configuration
        modeling_application (:obj:`str`): modeling application (e.g., ``XPP``)

    Returns:
        :obj:`list` of :obj:`int`: ids of projects
    """
    response = config['source_session'].get(config['source_api_endpoint'] + '/models?modeling_application={}'.format(modeling_application))
    response.raise_for_status()
    projects = response.json()
    projects.sort()
    return projects


def get_project(id, config):
    """ Get the details of a project from the source database and download the associated files

    Args:
        id (:obj:`int`): id of the project
        config (:obj:`dict`): configuration

    Returns:
        :obj:`dict`: detailed information about the project
    """
    # get information about the project
    response = config['source_session'].get(config['source_api_endpoint'] + '/models/' + str(id))
    response.raise_for_status()
    project = response.json()

    # get information about the papers
    for paper in project['model_paper']['value']:
        get_paper_metadata(paper, config)

    # download the files for the project by adding it as a submodule
    project_dirname = os.path.join(config['source_projects_dirname'], str(id))
    if not os.path.isdir(project_dirname):
        project_repo_url = '{}/{}.git'.format(config['source_projects_git_repository_organization'], id)
        repo = git.Repo(config['source_repository'])
        git.Submodule.add(repo, str(id), project_dirname, project_repo_url)
    elif config['update_project_sources']:
        project_repo = git.Repo(project_dirname)
        project_repo.head.reset(index=True, working_tree=True)
        # project_repo.remotes.origin.pull()

        raw_project_repo = git.Git(project_dirname)
        raw_project_repo.pull('origin', project_repo.branches[0].name)

    # return the details of the project
    return project


def get_paper_metadata(paper, config):
    """ Get metadata about a ModelDB paper

    Args:
        paper (:obj:`dict`): ModelDB paper
        config (:obj:`dict`): configuration
    """
    response = config['source_session'].get(config['source_api_endpoint'] + '/papers/' + str(paper['object_id']))
    response.raise_for_status()
    paper_details = response.json()

    if 'first_page' in paper_details:
        pages = paper_details['first_page']['value']
        if 'last_page' in paper_details:
            pages += '-' + paper_details['last_page']['value']
    else:
        pages = None

    title = paper_details['title']['value']
    if title.endswith('.'):
        title = title[0:-1]

    article = JournalArticle(
        authors=[author['object_name'] for author in paper_details['authors']['value']],
        title=title,
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


def get_metadata_for_project(project, project_dirname, config):
    """ Get additional metadata about a project

    * NCBI Taxonomy id of the organism
    * PubMed id, PubMed Central id and DOI for the reference
    * Open access figures for the reference

    Args:
        project (:obj:`dict`): information about a project
        project_dirname (:obj:`str`): path to the directory of files for the project
        config (:obj:`dict`): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`str`: description
            * :obj:`list` of :obj:`dict`: NCBI taxonomy identifiers and names
            * :obj:`list` of :obj:`dict`: structured information about the references
            * :obj:`list` of :obj:`dict`: thumbnails
    """
    metadata_filename = os.path.join(config['final_metadata_dirname'], str(project['id']) + '.yml')

    # read from cache
    if os.path.isfile(metadata_filename):
        with open(metadata_filename, 'r') as file:
            metadata = yaml.load(file, Loader=yaml.Loader)
        description = metadata.get('description', None)
        taxa = metadata.get('taxa', [])
        references = metadata.get('references', [])
        thumbnails = metadata.get('thumbnails', [])

        for thumbnail in thumbnails:
            thumbnail['local_filename'] = os.path.normpath(os.path.join(config['base_dirname'], thumbnail['local_filename']))

        return description, taxa, references, thumbnails

    # get images (gif, png, jpeg, jpg, webp)
    project_image_filenames = get_images_for_project(project_dirname)

    # get description from readme
    readme_filenames = case_insensitive_glob(os.path.join(project_dirname, '**', 'readme.*'), recursive=True)
    readme_filenames.sort(key=lambda filename: filename.count('/'))
    if readme_filenames:
        description = get_readme(readme_filenames[0], project['id'], project_dirname)
    else:
        description = None

    # get taxa
    taxa_ids = set()
    taxa = []
    for species in project.get('species', {}).get('value', []):
        taxon = TAXA.get(species['object_name'], None)
        if not taxon:
            raise ValueError("Taxonomy must be annotated for species '{}'".format(species['object_name']))
        taxa_ids.add(taxon['uri'])
        taxa.append(taxon)

    for region in project.get('region', {}).get('value', []):
        taxon = TAXA.get(region['object_name'], None)
        if taxon and taxon['uri'] not in taxa_ids:
            taxa_ids.add(taxon['uri'])
            taxa.append(taxon)

    # get citations and figures
    references = []
    thumbnails = []
    for paper in project.get('model_paper', {}).get('value', []):
        if paper['uris']['doi'] or paper['uris']['pubmed']:
            time.sleep(config['entrez_delay'])

            article = get_reference(
                paper['uris']['pubmed'],
                paper['uris']['doi'],
                cross_ref_session=config['cross_ref_session'],
            )

            # manually correct an invalid DOI
            # TODO: remove once corrected in ModelDB
            if paper['object_id'] == 39981:
                article.doi = '10.1523/JNEUROSCI.22-07-02963.2002'

            if article.doi:
                uri = 'http://identifiers.org/doi:{}'.format(article.doi)
            else:
                uri = 'http://identifiers.org/pubmed:{}'.format(article.pubmed_id)

            # Figures for the associated publication from open-access subset of PubMed Central
            if article.pubmed_central_id:
                graphics = get_pubmed_central_open_access_graphics(
                    article.pubmed_central_id,
                    os.path.join(config['source_thumbnails_dirname'], article.pubmed_central_id),
                    session=config['pubmed_central_open_access_session'],
                )
                for graphic in graphics:
                    thumbnails.append({
                        'id': graphic.id,
                        'local_filename': graphic.filename,
                        'archive_filename': os.path.join(
                            ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY,
                            os.path.basename(os.path.dirname(graphic.filename)),
                            os.path.basename(graphic.filename),
                        ),
                        'format': imghdr.what(graphic.filename),
                        'label': graphic.label,
                        'caption': graphic.caption,
                    })

        else:
            uri = paper['uris']['url']
            article = paper['citation']

        references.append({
            'uri': uri,
            'label': article.get_citation(),
        })

    # add images to thumbnails
    project_image_filenames.sort(key=lambda filename: (filename.count('/'), filename.lower()))
    for project_image_filename in project_image_filenames:
        thumbnails.append({
            'local_filename': project_image_filename,
            'archive_filename': os.path.relpath(project_image_filename, project_dirname),
            'format': imghdr.what(project_image_filename),
        })

    # save metadata
    metadata = {
        'description': description,
        'taxa': taxa,
        'references': references,
        'thumbnails': copy.deepcopy(thumbnails),
    }
    for thumbnail in metadata['thumbnails']:
        thumbnail['local_filename'] = os.path.relpath(thumbnail['local_filename'], config['base_dirname'])
    with open(metadata_filename, 'w') as file:
        file.write(yaml.dump(metadata))

    return (description, taxa, references, thumbnails)


def export_project_metadata_for_project_to_omex_metadata(project, description, taxa, references, thumbnails, metadata_filename, config):
    """ Export metadata about a project to an OMEX metadata RDF-XML file

    Args:
        project (:obj:`str`): information about the project
        description (:obj:`str`): description of the project
        taxa (:obj:`list` of :obj:`dict`): NCBI taxonomy identifier and name
        references (:obj:`list` of :obj:`dict`): structured information about the reference
        thumbnails (:obj:`list` of :obj:`dict`): thumbnails
        metadata_filename (:obj:`str`): path to save metadata
        config (:obj:`dict`): configuration
    """
    encodes = []
    for attr in MODELDB_BQBIOL_MAP:
        if attr['hasUri']:
            for object in project.get(attr['attribute'], {}).get('value', []):
                object_name = object['object_name']
                if attr['attribute'] == 'region':
                    if object_name in ['Generic', 'Unknown'] or object_name in TAXA:
                        continue  # pragma: no cover

                    object_name = object_name.partition(' (')[0]

                encodes.append({
                    'uri': 'http://modeldb.science/ModelList?id={}'.format(object['object_id']),
                    'label': object_name,
                })
        else:
            object_name = project.get(attr['attribute'], {}).get('value', None)
            if object_name:
                encodes.append({
                    'label': object_name,
                })

    creators = []
    for implemented_by in project.get('implemented_by', {}).get('value', []):
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
    if project.get('public_submitter_name', None):
        submitter = {
            'label': project['public_submitter_name']['value'],
            'uri': None,
        }
        if project.get('public_submitter_email', None):
            submitter['uri'] = 'mailto:' + project['public_submitter_email']['value']
        contributors.insert(0, submitter)

    created = dateutil.parser.parse(project['created'])
    last_updated = dateutil.parser.parse(project['ver_date'])

    metadata = {
        "uri": '.',
        "combine_archive_uri": BIOSIMULATIONS_ROOT_URI_FORMAT.format(project['id']),
        'title': project['name'],
        'abstract': project.get('notes', {}).get('value', None),
        'keywords': [
        ],
        'description': description,
        'taxa': taxa,
        'encodes': encodes,
        'thumbnails': [
            thumbnail['archive_filename']
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
                'uri': 'https://identifiers.org/modeldb:{}'.format(project['id']),
                'label': 'modeldb:{}'.format(project['id']),
            },
        ],
        'citations': references,
        'references': [],
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


def build_combine_archive_for_project(id, source_project_dirname, final_projects_dirname, archive_filename, extra_contents,
                                      max_number_of_simulation_steps=1000):
    """ Build a COMBINE/OMEX archive for a project including a SED-ML file

    Args:
        id (:obj:`str`): project id
        source_project_dirname (:obj:`str`): path to the directory of source files for the project
        final_projects_dirname (:obj:`str`): path to save the final files for the project
        archive_filename (:obj:`str`): path to save the COMBINE/OMEX archive
        extra_contents (:obj:`dict`): dictionary that maps the local path of each additional file that
            should be included in the arrchive to its intended location within the archive and format
        max_number_of_simulation_steps (:obj:`int`, optional): maximum number of simulation steps for generated SED-ML simulations

    Returns:
        :obj:`dict`: dictionary that maps the location of each SED document to the document
    """
    # initialize the directory for archive
    if os.path.isdir(final_projects_dirname):
        shutil.rmtree(final_projects_dirname)
    shutil.copytree(source_project_dirname, final_projects_dirname)
    ignore_filename_patterns = [
        '.git',
        '.DS_Store',
        'desktop.ini',
    ]
    for ignore_filename_pattern in ignore_filename_patterns:
        for ignore_filename in glob.glob(os.path.join(final_projects_dirname, '**', ignore_filename_pattern), recursive=True):
            os.remove(ignore_filename)

    # initialize COMBINE/OMEX archive for project
    archive = init_combine_archive_from_dir(source_project_dirname)

    # create simulations
    model_filenames = natsort.natsorted(
        case_insensitive_glob(os.path.join(source_project_dirname, '**', '*.ode'), recursive=True)
        + case_insensitive_glob(os.path.join(source_project_dirname, '**', '*.xpp'), recursive=True)
    )

    sed_docs = {}
    for model_filename in model_filenames:
        model_location = os.path.relpath(model_filename, source_project_dirname)

        sed_doc = create_sedml_for_xpp_file(id, source_project_dirname, model_location,
                                            max_number_of_simulation_steps=max_number_of_simulation_steps)

        sim_location = os.path.splitext(model_location)[0] + '.sedml'
        SedmlSimulationWriter().run(sed_doc, os.path.join(final_projects_dirname, sim_location))
        archive.contents.append(CombineArchiveContent(
            location=sim_location,
            format=CombineArchiveContentFormat.SED_ML.value,
            master=True,
        ))

        sed_docs[sim_location] = sed_doc

    # add metadata and thumbnails
    for local_path, extra_content in extra_contents.items():
        extra_content_dirname = os.path.dirname(os.path.join(final_projects_dirname, extra_content.location))
        if not os.path.isdir(extra_content_dirname):
            os.makedirs(extra_content_dirname)
        shutil.copyfile(local_path, os.path.join(final_projects_dirname, extra_content.location))
        archive.contents.append(extra_content)

    # save archive to file
    CombineArchiveWriter().run(archive, final_projects_dirname, archive_filename)

    return sed_docs


def create_sedml_for_xpp_file(project_id, project_dirname, rel_filename, max_number_of_simulation_steps=1000):
    """ Generate a SED-ML document for an XPP ODE file

    Args:
        project_id (:obj`int`): id of the parent project for the XPP ODE file
        project_dirname (:obj:`str`): path to the directory for the parent project of the XPP ODE file
        rel_filename (:obj:`str`): path to the XPP ODE file relative to :obj:`project_dirname`
        max_number_of_simulation_steps (:obj:`int`, optional): maximum number of simulation steps for generated SED-ML simulations

    Returns:
        :obj:`SedDocument`: SED-ML document for the XPP ODE file
    """
    abs_filename = os.path.join(project_dirname, rel_filename)

    sed_doc = SedDocument()

    # base model
    sed_base_model = Model(
        id='model',
        name='Model',
        source=os.path.basename(rel_filename),
        language=ModelLanguage.XPP.value,
    )
    sed_doc.models.append(sed_base_model)

    # model variants
    set_files = SET_FILE_MAP.get(project_id, {}).get(rel_filename, None)

    if set_files:
        for set_file in set_files:
            set_file['filename'] = os.path.join(project_dirname, set_file['filename'])
    else:
        set_files = [{
            'filename': None,
            'id': None,
            'name': None,
        }]

    for set_file in set_files:
        sed_params, sed_sims, sed_vars, sed_plots = get_parameters_variables_outputs_for_simulation(
            abs_filename, ModelLanguage.XPP, UniformTimeCourseSimulation, native_ids=True,
            model_language_options={
                ModelLanguage.XPP: {
                    'set_filename': set_file['filename'],
                    'max_number_of_steps': max_number_of_simulation_steps,
                },
            })

        sed_params = natsort.natsorted(sed_params, key=lambda param: param.target)
        sed_vars = natsort.natsorted(sed_vars, key=lambda var: (-1 if var.id is None else 1, var.id or ''))
        sed_plots = natsort.natsorted(sed_plots, key=lambda plot: plot.id)

        # model
        if set_file['id']:
            sed_model = Model(
                id='model_' + set_file['id'],
                name=set_file['name'],
                source='#' + sed_base_model.id,
                language=ModelLanguage.XPP.value,
                changes=copy.deepcopy(sed_params),
            )
            sed_doc.models.append(sed_model)

            for change in sed_model.changes:
                change.id += '_' + set_file['id']
        else:
            sed_model = sed_base_model
            sed_model.changes = sed_params

        for change in sed_model.changes:
            if change.target[0] == change.target[0].lower():
                change.name = 'Parameter ' + change.target
            else:
                change.name = 'Initial value of ' + change.target

        # simulation
        if set_file == set_files[0]:
            sed_sim = sed_sims[0]
            sed_sim.id = 'simulation'
            sed_sim.name = 'Simulation'
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

        data_gen_map = {}

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
            data_gen_map[var_id] = sed_data_gen

            sed_data_set = DataSet(
                id='data_set_{}'.format(var_id),
                name=var_id,
                label=var_id,
                data_generator=sed_data_gen,
            )
            if set_file['id']:
                sed_data_set.id += '_' + set_file['id']
            sed_report.data_sets.append(sed_data_set)

        if sed_plots:
            sed_plot = sed_plots[0]

            if set_file['id']:
                sed_plot.id += '_' + set_file['id']

            sed_plot.name = set_file['name']

            for sed_curve in list(sed_plot.curves):
                if set_file['id']:
                    sed_curve.id += '_' + set_file['id']

                x_data_generator_math = sed_curve.x_data_generator.math or 'T'
                y_data_generator_math = sed_curve.y_data_generator.math or 'T'

                sed_curve.x_data_generator = data_gen_map[x_data_generator_math]
                sed_curve.y_data_generator = data_gen_map[y_data_generator_math]

                if (
                    sed_curve.x_data_generator.variables[0].symbol == Symbol.time.value and
                    sed_curve.y_data_generator.variables[0].symbol == Symbol.time.value
                ):
                    sed_plot.curves.remove(sed_curve)

            if sed_plot.curves:
                sed_doc.outputs.append(sed_plot)

    return sed_doc


def init_combine_archive_from_dir(dirname):
    """ Initialize the specifications of COMBINE/OMEX archive for a ModelDB project from a directory for the project

    Args:
        dirname (:obj:`str`): directory

    Returns:
        :obj:`CombineArchive`: specifications for a COMBINE/OMEX archive for the project
    """
    archive = CombineArchive()
    filenames = glob.glob(os.path.join(dirname, '**', '*'), recursive=True)
    for filename in filenames:
        location = os.path.relpath(filename, dirname)
        if (
            os.path.isdir(filename)
            or os.path.basename(filename) in ['.DS_Store', 'desktop.ini']
            or filename.startswith('.git' + os.path.sep)
            or (os.path.sep + '.git' + os.path.sep) in filename
        ):
            continue  # pragma: no cover

        _, ext = os.path.splitext(location)
        if ext:
            ext = ext[1:]

        if ext.lower() in ['gif', 'jpeg', 'jpg', 'png', 'webp']:  # ignore image files because they will be included as 'extra_contents'
            continue  # pragma: no cover

        elif ext.lower() == 'xml':
            try:
                doc = lxml.etree.parse(filename)
                ns = doc.getroot().nsmap.get(None, None)
                if ns and ns.startswith('http://www.sbml.org/sbml/'):
                    uri = CombineArchiveContentFormat.SBML.value
                elif ns and ns.startswith('http://morphml.org/neuroml/schema'):
                    uri = CombineArchiveContentFormat.NeuroML.value
                else:
                    uri = CombineArchiveContentFormat.XML.value
            except lxml.etree.XMLSyntaxError:
                uri = CombineArchiveContentFormat.OTHER.value

        else:
            uri = FILE_EXTENSION_FORMAT_URI_MAP.get(ext.lower(), None)
            if uri is None:
                uri = CombineArchiveContentFormat.OTHER.value
                msg = 'Format URI for `{}` is not known'.format(filename)
                warnings.warn(msg, UserWarning)

        archive.contents.append(CombineArchiveContent(
            location=location,
            format=uri,
        ))
    return archive


def import_projects(config):
    """ Download the source database, convert into COMBINE/OMEX archives, simulate the archives, and submit them to BioSimulations

    Args:
        config (:obj:`dict`): configuration
    """

    # create directories for source files, thumbnails, projects, and simulation results
    make_directories(config)

    # read import status file
    if os.path.isfile(config['status_filename']):
        with open(config['status_filename'], 'r') as file:
            status = yaml.load(file, Loader=yaml.Loader)
    else:
        status = {}

    # get a list of the ids of all projects available in the source database
    project_ids = get_project_ids(config, MODELING_APPLICATION)

    # filter to selected projects
    if config['project_ids'] is not None:
        project_ids = list(filter(lambda project_id: project_id in config['project_ids'], project_ids))

    # limit the number of projects to import
    project_ids = project_ids[config['first_project']:]
    project_ids = project_ids[0:config['max_projects']]

    # get the details of each project
    projects = []
    update_times = {}
    print('Retrieving {} projects ...'.format(len(project_ids)))
    for i_project, project_id in enumerate(project_ids):
        print('  {}: {} ...'.format(i_project + 1, project_id), end='')
        sys.stdout.flush()

        # update status
        update_times[str(project_id)] = datetime.datetime.utcnow()

        # get the details of the project and download it from the source database
        project = get_project(project_id, config)
        projects.append(project)

        print(' done')

    # filter out projects that don't need to be imported because they've already been imported and haven't been updated
    if not config['update_simulation_runs']:
        projects = list(filter(
            lambda project:
            (
                str(project['id']) not in status
                or not status[str(project['id'])]['runbiosimulationsId']
                or (
                    (dateutil.parser.parse(project['ver_date']) + datetime.timedelta(1))
                    > dateutil.parser.parse(status[str(project['id'])]['updated'])
                )
            ),
            projects
        ))

    # filter out projects with issues
    with open(config['issues_filename'], 'r') as file:
        issues = yaml.load(file, Loader=yaml.Loader)
    projects = list(filter(lambda project: int(project['id']) not in issues, projects))

    # get authorization for BioSimulations API
    auth = biosimulators_utils.biosimulations.utils.get_authorization_for_client(
        config['biosimulations_api_client_id'], config['biosimulations_api_client_secret'])

    # download projects, convert them to COMBINE/OMEX archives, simulate them, and deposit them to the BioSimulations database
    print('Importing {} projects ...'.format(len(projects)))
    for i_project, project in enumerate(projects):
        print('  {}: {} ...'.format(i_project + 1, project['id']))

        prev_duration = status.get(str(project['id']), {}).get('duration', None)
        simulate_project = config['simulate_projects'] and (
            config['update_combine_archives']
            or config['update_simulations']
            or prev_duration is None
        )
        runbiosimulations_id, duration, biosimulations_id = import_project(project, simulate_project, auth, config)

        # output status
        print('    Saving status ...', end='')
        sys.stdout.flush()

        if duration is None:
            duration = prev_duration

        if config['dry_run']:
            runbiosimulations_id = status.get(str(project['id']), {}).get('runbiosimulationsId', None)
            updated = status.get(str(project['id']), {}).get('updated', None)
        else:
            updated = str(update_times[str(project['id'])])

        status[str(project['id'])] = {
            'created': status.get(str(project['id']), {}).get('created', str(update_times[str(project['id'])])),
            'updated': updated,
            'duration': duration,
            'runbiosimulationsId': runbiosimulations_id,
            'biosimulationsId': biosimulations_id,
        }
        with open(config['status_filename'], 'w') as file:
            file.write(yaml.dump(status))

        print(' done')

        print('    done')
    print('{} projects completely successfully!'.format(len(projects)))


def make_directories(config):
    """ Create directories for source files, thumbnails, projects, and simulation results

    Args:
        config (:obj:`dict`): configuration
    """
    if not os.path.isdir(config['source_projects_dirname']):
        os.makedirs(config['source_projects_dirname'])
    if not os.path.isdir(config['source_thumbnails_dirname']):
        os.makedirs(config['source_thumbnails_dirname'])

    if not os.path.isdir(config['final_metadata_dirname']):
        os.makedirs(config['final_metadata_dirname'])
    if not os.path.isdir(config['final_projects_dirname']):
        os.makedirs(config['final_projects_dirname'])
    if not os.path.isdir(config['final_simulation_results_dirname']):
        os.makedirs(config['final_simulation_results_dirname'])


def import_project(project, simulate, auth, config):
    """ Import a project into BioSimulations

    Args:
        project (:obj:`dict`): project
        simulate (:obj:`bool`): whether to simulate the project
        auth (:obj:`str`): authorization header for the BioSimulations API
        config (:obj:`dict`): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`str`: runBioSimulations id for the run of the project
            * :obj:`float`: duration of the simulation of the project
            * :obj:`str`: BioSimulations id for the run of the project
    """
    source_project_dirname = os.path.join(config['source_projects_dirname'], str(project['id']))
    final_projects_dirname = os.path.join(config['final_projects_dirname'], str(project['id']))

    # get additional metadata about the project
    print('    Getting metadata ...', end='')
    sys.stdout.flush()

    description, taxa, references, thumbnails = get_metadata_for_project(project, source_project_dirname, config)

    print(' done')

    # export metadata to RDF
    print('    Exporting metadata ...', end='')
    sys.stdout.flush()

    project_metadata_filename = os.path.join(config['final_metadata_dirname'], str(project['id']) + '.rdf')
    if not os.path.isfile(project_metadata_filename) or config['update_combine_archives']:
        export_project_metadata_for_project_to_omex_metadata(project, description, taxa, references, thumbnails,
                                                             project_metadata_filename, config)

    print(' done')

    # package project into COMBINE/OMEX archive
    print('    Generating COMBINE/OMEX archive ...', end='')
    sys.stdout.flush()

    project_filename = os.path.join(config['final_projects_dirname'], str(project['id']) + '.omex')
    if not os.path.isfile(project_filename) or config['update_combine_archives']:
        extra_contents = {}

        extra_contents[project_metadata_filename] = CombineArchiveContent(
            location='metadata.rdf',
            format=CombineArchiveContentFormat.OMEX_METADATA.value,
        )

        for thumbnail in thumbnails:
            extra_contents[thumbnail['local_filename']] = CombineArchiveContent(
                location=thumbnail['archive_filename'],
                format='http://purl.org/NET/mediatypes/image/' + thumbnail['format'],
            )

        sed_docs = build_combine_archive_for_project(project['id'], source_project_dirname, final_projects_dirname,
                                                     project_filename,
                                                     extra_contents=extra_contents,
                                                     max_number_of_simulation_steps=config['max_number_of_simulation_steps'])

        for sed_doc_location, sed_doc in sed_docs.items():
            sed_sim = sed_doc.simulations[0]
            if sed_sim.number_of_steps <= 1:
                msg = 'Simulation {} of {} only has {} steps'.format(sed_doc_location, project['id'], sed_sim.number_of_steps)
                raise ValueError(msg)

            for output in sed_doc.outputs:
                if isinstance(output, Report):
                    if len(output.data_sets) <= 2:
                        msg = 'Report {} of {} of {} only has {} outputs:\n  - {}'.format(
                            output.id, sed_doc_location, project['id'], len(output.data_sets),
                            '  - '.join(sorted(data_set.id for data_set in output.data_sets)),
                        )
                        raise ValueError(msg)

    else:
        sed_docs = None

    print(' done')

    # simulate COMBINE/OMEX archives
    print('    Simulating project ...', end='')
    sys.stdout.flush()

    if simulate:
        out_dirname = os.path.join(config['final_simulation_results_dirname'], str(project['id']))
        biosimulators_utils_config = Config(COLLECT_COMBINE_ARCHIVE_RESULTS=True, VERBOSE=True, DEBUG=True)  # TODO: remove
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", BioSimulatorsWarning)
            results, log = biosimulators_xpp.exec_sedml_docs_in_combine_archive(
                project_filename, out_dirname, config=biosimulators_utils_config)
        if log.exception:
            raise log.exception
        duration = log.duration

        # verify simulation results
        if sed_docs:
            for sed_doc_location, sed_doc in sed_docs.items():
                sed_doc_results = results[sed_doc_location]
                sed_sim = sed_doc.simulations[0]
                for output in sed_doc.outputs:
                    if isinstance(output, Report):
                        report_results = sed_doc_results[output.id]
                        expected_data_set_ids = set(data_set.id for data_set in output.data_sets)
                        data_set_ids = set(report_results.keys())

                        missing_data_set_ids = expected_data_set_ids.difference(data_set_ids)
                        extra_data_set_ids = data_set_ids.difference(expected_data_set_ids)

                        if missing_data_set_ids:
                            msg = (
                                '{} data sets were not produced for report {} of {} of {}:\n  - {}'
                            ).format(
                                len(missing_data_set_ids),
                                output.id,
                                sed_doc_location,
                                project['id'],
                                '\n  - '.join(sorted(missing_data_set_ids)),
                            )
                            raise ValueError(msg)

                        if extra_data_set_ids:
                            msg = (
                                '{} extra data sets were produced for report {} of {} of {}:\n  - {}'
                            ).format(
                                len(extra_data_set_ids),
                                output.id,
                                sed_doc_location,
                                project['id'],
                                '\n  - '.join(sorted(extra_data_set_ids)),
                            )
                            raise ValueError(msg)

                        for data_set_id, data_set_results in report_results.items():
                            if data_set_results.shape != (sed_sim.number_of_steps + 1,):
                                msg = 'Data set {} of report {} of {} of {} has shape ({}), not ({})'.format(
                                    data_set_id, output.id, sed_doc_location,
                                    project['id'],
                                    ', '.join(str(dim_len) for dim_len in data_set_results.shape),
                                    sed_sim.number_of_steps + 1,
                                )
                                raise ValueError(msg)

                            if any(numpy.isnan(data_set_results)):
                                raise ValueError('The result of data set {} of report {} of {} includes NaN.')

                        time_results = report_results[output.data_sets[0].id]
                        expected_time_results = numpy.linspace(
                            sed_sim.output_start_time, sed_sim.output_end_time, sed_sim.number_of_steps + 1)
                        time_results_error = numpy.linalg.norm(time_results - expected_time_results, ord=1) / (sed_sim.number_of_steps + 1)
                        if time_results_error > 5e-3:
                            msg = 'The points of the report of {} of {} of {} are invalid (err = {}):\n  - {}'.format(
                                output.id, sed_doc_location, project['id'],
                                time_results_error,
                                '\n  - '.join('{}: {}'.format(x, y) for x, y in zip(time_results, expected_time_results)),
                            )
                            raise ValueError(msg)

    else:
        duration = None

    print(' done')

    # submit COMBINE/OMEX archive to BioSimulations
    print('    Submitting project to BioSimulations ...', end='')
    sys.stdout.flush()

    run_name = project['name']
    if config['publish_projects']:
        project_id = get_biosimulations_project_id(project['id'])
    else:
        project_id = None

    # get S3 bucket to save archives
    s3 = boto3.resource('s3',
                        endpoint_url=config['bucket_endpoint'],
                        aws_access_key_id=config['bucket_access_key_id'],
                        aws_secret_access_key=config['bucket_secret_access_key'],
                        verify=False)
    bucket = s3.Bucket(config['bucket_name'])

    project_bucket_key = '{}.omex'.format(str(project['id']))
    project_url = '{}/{}/{}'.format(config['bucket_endpoint'], config['bucket_name'], project_bucket_key)

    if config['dry_run']:
        runbiosimulations_id = None
    else:
        bucket.upload_file(project_filename, project_bucket_key)
        runbiosimulations_id = biosimulators_utils.biosimulations.utils.run_simulation_project(
            run_name, project_url, BIOSIMULATORS_SIMULATOR_ID, project_id=project_id, purpose='academic', auth=auth)

    print(' done')

    return runbiosimulations_id, duration, project_id
