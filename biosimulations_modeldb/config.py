import datetime
import dotenv
import os
import pkg_resources
import requests_cache
import yaml


__all__ = ['get_config']


def get_config(
        source_api_endpoint='http://modeldb.science/api/v1',
        source_projects_git_repository_organization='https://github.com/ModelDBRepository',
        base_dirname=None,
        source_dirname=None,
        sessions_dirname=None,
        final_dirname=None,
        curators_filename=None,
        issues_filename=None,
        status_filename=None,
        project_ids=None,
        first_project=0,
        max_projects=None,
        update_project_sources=False,
        update_combine_archives=False,
        update_simulations=False,
        update_simulation_runs=False,
        simulate_projects=True,
        publish_projects=True,
        entrez_delay=5.,
        max_number_of_simulation_steps=1000,
        bucket_endpoint=None,
        bucket_name=None,
        bucket_access_key_id=None,
        bucket_secret_access_key=None,
        biosimulations_api_client_id=None,
        biosimulations_api_client_secret=None,
        dry_run=False,
):
    """ Get a configuration

    Args:
        source_api_endpoint (obj:`str`, optional): endpoint for retrieving metadata about ModelDB projects
        source_projects_git_repository_organization (obj:`str`, optional): organization for git repositories for ModelDB projects
        base_dirname (:obj:`str`, optional): base directory for data
        source_dirname (obj:`str`, optional): directory where source projects, metabolic flux maps, and thumbnails should be stored
        sessions_dirname (obj:`str`, optional): directory where cached HTTP sessions should be stored
        final_dirname (obj:`str`, optional): directory where created SED-ML, metadata, and COMBINE/OMEX archives should be stored
        curators_filename (obj:`str`, optional): path which describes the people who helped curator the repository
        issues_filename (obj:`str`, optional): path to issues which prevent some projects from being imported
        status_filename (obj:`str`, optional): path to save the import status of each project
        project_ids (:obj:`list` of :obj:`str`, optional): ids of projects to import
        first_project (:obj:`int`, optional): iteration through projects at which to begin importing
        max_projects (:obj:`int`, optional): maximum number of projects to download, convert, execute, and submit; used for testing
        update_project_sources (:obj:`bool`, optional): whether to update the source files for the projects; used for testing
        update_combine_archives (:obj:`bool`, optional): whether to update COMBINE archives even if they already exist; used for testing
        update_simulations (:obj:`bool`, optional): whether to re-run COMBINE archives even if they have already been run; used for testing
        update_simulation_runs (:obj:`bool`, optional): whether to update projects even if they have already been imported; used for testing
        simulate_projects (:obj:`bool`, optional): whether to simulate projects; used for testing
        publish_projects (:obj:`bool`, optional): whether to pushlish projects; used for testing
        entrez_delay (:obj:`float`, optional): delay in between Entrez queries
        max_number_of_simulation_steps (:obj:`int`, optional): maximum number of simulation steps for generated SED-ML simulations
        bucket_endpoint (:obj:`str`, optional): endpoint for storage bucket
        bucket_name (:obj:`str`, optional): name of storage bucket
        bucket_access_key_id (:obj:`str`, optional): key id for storage bucket
        bucket_secret_access_key (:obj:`str`, optional): access key for storage bucket
        biosimulations_api_client_id (:obj:`str`, optional): id for client to the BioSimulations API
        biosimulations_api_client_secret (:obj:`str`, optional): secret for client to the BioSimulations API
        dry_run (:obj:`bool`, optional): whether to submit projects to BioSimulations or not; used for testing

    Returns:
        obj:`dict`: configuration
    """

    env = {
        **dotenv.dotenv_values("secret.env"),
        **os.environ,
    }

    if base_dirname is None:
        base_dirname = env.get('BASE_DIRNAME', pkg_resources.resource_filename('biosimulations_modeldb', '.'))
    if source_dirname is None:
        source_dirname = env.get('SOURCE_DIRNAME', os.path.join(base_dirname, 'source'))
    if sessions_dirname is None:
        sessions_dirname = env.get('SESSIONS_DIRNAME', os.path.join(base_dirname, 'source'))
    if final_dirname is None:
        final_dirname = env.get('FINAL_DIRNAME', os.path.join(base_dirname, 'final'))
    if curators_filename is None:
        curators_filename = env.get('CURATORS_FILENAME', os.path.join(base_dirname, 'final', 'curators.yml'))
    if issues_filename is None:
        issues_filename = env.get('ISSUES_FILENAME', os.path.join(base_dirname, 'final', 'issues.yml'))
    if status_filename is None:
        status_filename = env.get('STATUS_FILENAME', os.path.join(base_dirname, 'final', 'status.yml'))

    if bucket_endpoint is None:
        bucket_endpoint = env.get('BUCKET_ENDPOINT')
    if bucket_name is None:
        bucket_name = env.get('BUCKET_NAME')
    if bucket_access_key_id is None:
        bucket_access_key_id = env.get('BUCKET_ACCESS_KEY_ID')
    if bucket_secret_access_key is None:
        bucket_secret_access_key = env.get('BUCKET_SECRET_ACCESS_KEY')

    if biosimulations_api_client_id is None:
        biosimulations_api_client_id = env.get('BIOSIMULATIONS_API_CLIENT_ID')
    if biosimulations_api_client_secret is None:
        biosimulations_api_client_secret = env.get('BIOSIMULATIONS_API_CLIENT_SECRET')

    with open(curators_filename, 'r') as file:
        curators = yaml.load(file, Loader=yaml.Loader)

    return {
        'source_api_endpoint': source_api_endpoint,
        'source_projects_git_repository_organization': source_projects_git_repository_organization,

        'base_dirname': base_dirname,

        'source_repository': os.path.join(base_dirname, '..'),
        'source_projects_dirname': os.path.join(source_dirname, 'projects'),
        'source_thumbnails_dirname': os.path.join(source_dirname, 'thumbnails'),

        'final_metadata_dirname': os.path.join(final_dirname, 'metadata'),
        'final_projects_dirname': os.path.join(final_dirname, 'projects'),
        'final_simulation_results_dirname': os.path.join(final_dirname, 'simulation-results'),

        'curators_filename': curators_filename,
        'curators': curators,
        'issues_filename': issues_filename,
        'status_filename': status_filename,

        'source_session': requests_cache.CachedSession(
            os.path.join(sessions_dirname, 'source'),
            expire_after=datetime.timedelta(4 * 7)),
        'cross_ref_session': requests_cache.CachedSession(
            os.path.join(sessions_dirname, 'crossref'),
            expire_after=datetime.timedelta(4 * 7)),
        'pubmed_central_open_access_session': requests_cache.CachedSession(
            os.path.join(sessions_dirname, 'pubmed-central-open-access'),
            expire_after=datetime.timedelta(4 * 7)),

        'project_ids': project_ids,
        'first_project': first_project,
        'max_projects': max_projects,
        'update_project_sources': update_project_sources,
        'update_combine_archives': update_combine_archives,
        'update_simulations': update_simulations,
        'update_simulation_runs': update_simulation_runs,
        'simulate_projects': simulate_projects,
        'publish_projects': publish_projects,
        'entrez_delay': entrez_delay,
        'max_number_of_simulation_steps': max_number_of_simulation_steps,
        'bucket_endpoint': bucket_endpoint,
        'bucket_name': bucket_name,
        'bucket_access_key_id': bucket_access_key_id,
        'bucket_secret_access_key': bucket_secret_access_key,
        'biosimulations_api_client_id': biosimulations_api_client_id,
        'biosimulations_api_client_secret': biosimulations_api_client_secret,
        'dry_run': dry_run,
    }
