import datetime
import dotenv
import os
import pkg_resources
import requests_cache
import yaml


__all__ = ['get_config']

BASE_DIR = pkg_resources.resource_filename('biosimulations_modeldb', '.')


def get_config(
        source_api_endpoint='http://modeldb.science/api/v1',
        source_models_git_repository_organization='https://github.com/ModelDBRepository',
        source_dirname=None,
        sessions_dirname=None,
        final_dirname=None,
        curators_filename=None,
        issues_filename=None,
        status_filename=None,
        max_models=None,
        update_combine_archives=False,
        update_simulation_runs=False,
        simulate_models=True,
        publish_models=True,
        entrez_delay=5.,
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
        source_api_endpoint (obj:`str`, optional): endpoint for retrieving metadata about ModelDB models
        source_models_git_repository_organization (obj:`str`, optional): organization for git repositories for ModelDB models
        source_dirname (obj:`str`, optional): directory where source models, metabolic flux maps, and thumbnails should be stored
        sessions_dirname (obj:`str`, optional): directory where cached HTTP sessions should be stored
        final_dirname (obj:`str`, optional): directory where created SED-ML, metadata, and COMBINE/OMEX archives should be stored
        curators_filename (obj:`str`, optional): path which describes the people who helped curator the repository
        issues_filename (obj:`str`, optional): path to issues which prevent some models from being imported
        status_filename (obj:`str`, optional): path to save the import status of each model
        max_models (:obj:`int`, optional): maximum number of models to download, convert, execute, and submit; used for testing
        update_combine_archives (:obj:`bool`, optional): whether to update COMBINE archives even if they already exist; used for testing
        update_simulation_runs (:obj:`bool`, optional): whether to update models even if they have already been imported; used for testing
        simulate_models (:obj:`bool`, optional): whether to simulate models; used for testing
        publish_models (:obj:`bool`, optional): whether to pushlish models; used for testing
        entrez_delay (:obj:`float`, optional): delay in between Entrez queries
        bucket_endpoint (:obj:`str`, optional): endpoint for storage bucket
        bucket_name (:obj:`str`, optional): name of storage bucket
        bucket_access_key_id (:obj:`str`, optional): key id for storage bucket
        bucket_secret_access_key (:obj:`str`, optional): access key for storage bucket
        biosimulations_api_client_id (:obj:`str`, optional): id for client to the BioSimulations API
        biosimulations_api_client_secret (:obj:`str`, optional): secret for client to the BioSimulations API
        dry_run (:obj:`bool`, optional): whether to submit models to BioSimulations or not; used for testing

    Returns:
        obj:`dict`: configuration
    """

    env = {
        **dotenv.dotenv_values("secret.env"),
        **os.environ,
    }

    if source_dirname is None:
        source_dirname = env.get('SOURCE_DIRNAME', os.path.join(BASE_DIR, 'source'))
    if sessions_dirname is None:
        sessions_dirname = env.get('SESSIONS_DIRNAME', os.path.join(BASE_DIR, 'source'))
    if final_dirname is None:
        final_dirname = env.get('FINAL_DIRNAME', os.path.join(BASE_DIR, 'final'))
    if curators_filename is None:
        curators_filename = env.get('CURATORS_FILENAME', os.path.join(BASE_DIR, 'final', 'curators.yml'))
    if issues_filename is None:
        issues_filename = env.get('ISSUES_FILENAME', os.path.join(BASE_DIR, 'final', 'issues.yml'))
    if status_filename is None:
        status_filename = env.get('STATUS_FILENAME', os.path.join(BASE_DIR, 'final', 'status.yml'))

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
        'source_models_git_repository_organization': source_models_git_repository_organization,

        'source_repository': os.path.join(source_dirname, '..', '..'),
        'source_models_dirname': os.path.join(source_dirname, 'models'),
        'source_thumbnails_dirname': os.path.join(source_dirname, 'thumbnails'),

        'final_visualizations_dirname': os.path.join(final_dirname, 'visualizations'),
        'final_metadata_dirname': os.path.join(final_dirname, 'metadata'),
        'final_projects_dirname': os.path.join(final_dirname, 'projects'),
        'final_simulation_results_dirname': os.path.join(final_dirname, 'simulation-results'),

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

        'max_models': max_models,
        'update_combine_archives': update_combine_archives,
        'update_simulation_runs': update_simulation_runs,
        'simulate_models': simulate_models,
        'publish_models': publish_models,
        'entrez_delay': entrez_delay,
        'bucket_endpoint': bucket_endpoint,
        'bucket_name': bucket_name,
        'bucket_access_key_id': bucket_access_key_id,
        'bucket_secret_access_key': bucket_secret_access_key,
        'biosimulations_api_client_id': biosimulations_api_client_id,
        'biosimulations_api_client_secret': biosimulations_api_client_secret,
        'dry_run': dry_run,
    }