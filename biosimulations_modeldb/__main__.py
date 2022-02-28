from .config import get_config
from .core import import_projects
from ._version import __version__
from biosimulators_utils.config import get_config as get_biosimulators_config
from biosimulators_utils.warnings import warn
import biosimulators_utils.biosimulations.utils
import cement
import collections
import requests
import requests.exceptions
import simplejson.errors
import sys
import termcolor
import yaml


class BaseController(cement.Controller):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = "Utilities for publishing ModelDB to BioSimulations"
        help = "Utilities for publishing ModelDB to BioSimulations"
        arguments = [
            (['-v', '--version'], dict(
                action='version',
                version=__version__,
            )),
        ]

    @cement.ex(hide=True)
    def _default(self):
        self._parser.print_help()


class RunAndPublishProjectsController(cement.Controller):
    """ Publish projects from ModelDB to BioSimulations

    * Download projects
    * Download metadata
    * Generate SED-ML files for projects
    * Expand taxonomy metadata using NCBI Taxonomy
    * Expand citation metadata using PubMed and CrossRef
    * Obtain thumbnail images using PubMed Central
    * Encode metadata into OMEX metadata files
    * Package project into COMBINE/OMEX archives
    * Submit simulation runs for archives to runBioSimulations
    * Publish simulation runs to BioSimulations
    """

    class Meta:
        label = 'run-projects-and-publish'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Publish projects from ModelDB to BioSimulations"
        description = "Publish projects from ModelDB to BioSimulations"
        arguments = [
            (
                ['--project'],
                dict(
                    type=int,
                    nargs='+',
                    action='extend',
                    help='Id of a project to run and publish. Used for testing.',
                ),
            ),
            (
                ['--first-project'],
                dict(
                    type=int,
                    default=1,
                    help='Iteration (1-based) through projects at which to begin importing. Used for testing.',
                ),
            ),
            (
                ['--max-projects'],
                dict(
                    type=int,
                    default=None,
                    help='Maximum number of projects to import. Used for testing.',
                ),
            ),
            (
                ['--update-project-sources'],
                dict(
                    action='store_true',
                    help='If set, update the source files for the projects. Used for testing.'
                ),
            ),
            (
                ['--update-combine-archives'],
                dict(
                    action='store_true',
                    help='If set, update COMBINE/OMEX archives even if they have already been assembled. Used for testing.'
                ),
            ),
            (
                ['--update-simulations'],
                dict(
                    action='store_true',
                    help='If set, re-run COMBINE/OMEX archives even if they have already been run. Used for testing.'
                ),
            ),
            (
                ['--update-simulation-runs'],
                dict(
                    action='store_true',
                    help='If set, update simulation runs even if they have already been submitted. Used for testing.'
                ),
            ),
            (
                ['--skip-simulation'],
                dict(
                    action='store_true',
                    help='If set, do not simulate projects. Used for testing.',
                ),
            ),
            (
                ['--skip-publication'],
                dict(
                    action='store_true',
                    help='If set, do not publish projects. Used for testing.',
                ),
            ),
            (
                ['--dry-run'],
                dict(
                    action='store_true',
                    help='If set, do not submit projects to BioSimulations. Used for testing.'
                ),
            ),
        ]

    @ cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs

        config = get_config(project_ids=args.project,
                            first_project=args.first_project - 1,
                            max_projects=args.max_projects,
                            update_project_sources=args.update_project_sources,
                            update_combine_archives=args.update_combine_archives,
                            update_simulations=args.update_simulations,
                            update_simulation_runs=args.update_simulation_runs,
                            simulate_projects=not args.skip_simulation,
                            publish_projects=not args.skip_publication,
                            dry_run=args.dry_run)

        import_projects(config)


class PublishRunsController(cement.Controller):
    """ Publish runs of simulations of ModelDB projects to BioSimulations """

    class Meta:
        label = 'publish-runs'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Publish runs of simulations to BioSimulations"
        description = "Publish runs of simulations of ModelDB projects to BioSimulations"
        arguments = [
            (
                ['--project'],
                dict(
                    type=int,
                    nargs='+',
                    action='extend',
                    help='Id of a project to publish. Used for testing.',
                ),
            ),
            (
                ['--ignore-errors'],
                dict(
                    action='store_true',
                    help='If set, publish runs even if some did not succeed. Used for testing.'
                ),
            ),
        ]

    @ cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs

        config = get_config()
        biosimulators_config = get_biosimulators_config()

        # read simulation runs
        projects_filename = config['status_filename']
        with open(projects_filename, 'r') as file:
            projects = yaml.load(file, Loader=yaml.Loader)

        # filter to selected projects
        if args.project is not None:
            projects = {id: project for id, project in projects.items() if int(id) in args.project}

        # check status
        failures = collections.OrderedDict()
        for id, project in projects.items():
            if project['runbiosimulationsId']:
                response = requests.get(biosimulators_config.BIOSIMULATIONS_API_ENDPOINT + 'runs/' + project['runbiosimulationsId'])
                response.raise_for_status()
                project['runbiosimulationsStatus'] = response.json()['status']
                if project['runbiosimulationsStatus'] != 'SUCCEEDED':
                    failures[id] = '{}: {}'.format(id, project['runbiosimulationsStatus'])
            else:
                failures[id] = '{}: {}'.format(id, 'not submitted')
        if len(failures):
            msg = '{} simulation runs did not succeed:\n  {}'.format(len(failures), '\n  '.join(sorted(failures.values())))
            if args.ignore_errors:
                warn(msg, UserWarning)
            else:
                raise SystemExit(msg)

        # login to publish projects
        auth_headers = {
            'Authorization': biosimulators_utils.biosimulations.utils.get_authorization_for_client(
                config['biosimulations_api_client_id'],
                config['biosimulations_api_client_secret'],
            )
        }

        # publish projects
        print('Publishing or updating {} projects ...'.format(len(projects)))
        projects_already_up_to_date = []
        create_projects_succeeded = []
        update_projects_succeeded = []
        create_projects_failed = []
        update_projects_failed = []
        for i_project, (id, project) in enumerate(projects.items()):
            print('  {}: {} ... '.format(i_project + 1, id), end='')
            sys.stdout.flush()

            if id in failures:
                print('run failed.')
                continue

            if project.get('biosimulationsId', None) is not None:
                endpoint = biosimulators_config.BIOSIMULATIONS_API_ENDPOINT + 'projects/' + project['biosimulationsId']

                response = requests.get(endpoint)

                if response.status_code == 200:
                    if response.json()['simulationRun'] == project['runbiosimulationsId']:
                        api_method = None
                        print('already up to date. ', end='')
                        sys.stdout.flush()

                    else:
                        api_method = requests.put
                        print('updating ... ', end='')
                        sys.stdout.flush()

                else:
                    api_method = requests.post
                    print('publishing ... ', end='')
                    sys.stdout.flush()

            else:
                api_method = requests.post
                print('publishing ... ', end='')
                sys.stdout.flush()

            if api_method:
                response = api_method(endpoint,
                                      headers=auth_headers,
                                      json={
                                          'id': project['biosimulationsId'],
                                          'simulationRun': project['runbiosimulationsId']
                                      })
                try:
                    response.raise_for_status()
                    print('done.')
                    if api_method == requests.post:
                        create_projects_succeeded.append(id)
                    else:
                        update_projects_succeeded.append(id)

                except requests.exceptions.RequestException as exception:
                    print(termcolor.colored('failed: {}.'.format(str(exception)), 'red'))
                    try:
                        print(termcolor.colored('    ' + response.json()['error'][0]['detail'].replace('\n', '\n    '), 'red'))
                    except simplejson.errors.JSONDecodeError:
                        pass
                    if api_method == requests.post:
                        create_projects_failed.append(id)
                    else:
                        update_projects_failed.append(id)

            else:
                print('done.')
                projects_already_up_to_date.append(id)
        print('')

        # print message
        if create_projects_failed or update_projects_failed or failures:
            print('{} projects were already up to date.'.format(len(projects_already_up_to_date)))
            print('{} projects were successfully created.'.format(len(create_projects_succeeded)))
            print('{} projects were successfully updated.'.format(len(update_projects_succeeded)))
            print(termcolor.colored('{} projects could not be created.'.format(len(create_projects_failed)), 'red'))
            print(termcolor.colored('{} projects could not be updated.'.format(len(update_projects_failed)), 'red'))
            print(termcolor.colored('{} projects could not be created or updated because the run failed.'.format(
                len(failures)), 'yellow'))
        else:
            print(termcolor.colored('All {} projects were successfully published or updated or were already up to date!'.format(
                len(projects)), 'green'))


class VerifyPublicationController(cement.Controller):
    """ Verify that projects from ModelDB have been successfully published to BioSimulations """

    class Meta:
        label = 'verify-publication'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Verify that projects have been published to BioSimulations"
        description = "Verify that projects from ModelDB have been successfully published to BioSimulations"
        arguments = [
            (
                ['--project'],
                dict(
                    type=int,
                    nargs='+',
                    action='extend',
                    help='Id of a project to verify. Used for testing.',
                ),
            ),
        ]

    @ cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs

        config = get_config()
        biosimulators_config = get_biosimulators_config()

        # read source projects
        source_projects_filename = config['status_filename']
        with open(source_projects_filename, 'r') as file:
            source_projects = yaml.load(file, Loader=yaml.Loader)

        # filter to selected projects
        if args.project is not None:
            source_projects = {id: project for id, project in source_projects.items() if int(id) in args.project}

        # get BioSimulations projects
        biosimulations_api_endpoint = biosimulators_config.BIOSIMULATIONS_API_ENDPOINT
        response = requests.get(biosimulations_api_endpoint + 'projects')
        response.raise_for_status()
        biosimulations_projects = {
            project['id']: project
            for project in response.json()
        }

        # check all ModelDB projects were published
        errors = []
        for source_project_id, source_project in source_projects.items():
            if source_project['biosimulationsId'] not in biosimulations_projects:
                if source_project['runbiosimulationsId']:
                    biosimulations_api_endpoint = biosimulators_config.BIOSIMULATIONS_API_ENDPOINT
                    response = requests.get(biosimulations_api_endpoint + 'runs/{}'.format(source_project['runbiosimulationsId']))
                    response.raise_for_status()
                    run_status = response.json()['status']
                else:
                    run_status = 'not submitted'
                errors.append('{}: has not been published. The status of run `{}` is `{}`.'.format(
                    source_project_id, source_project['runbiosimulationsId'], run_status))
            elif biosimulations_projects[source_project['biosimulationsId']]['simulationRun'] != source_project['runbiosimulationsId']:
                biosimulations_api_endpoint = biosimulators_config.BIOSIMULATIONS_API_ENDPOINT
                url = biosimulations_api_endpoint + 'projects/{}'.format(source_project['biosimulationsId'])
                response = requests.get(url)
                try:
                    response.raise_for_status()
                    owner = response.json().get('owner', {}).get('name', None)

                    if owner != 'ModelDB':
                        reason = 'Project id has already been claimed.'
                    else:
                        reason = 'Project is published with run `{}`.'.format(response.json()['simulationRun'])
                except requests.exceptions.RequestException:
                    reason = 'Project could not be found'

                errors.append('{}: not published as run {}. {}'.format(source_project_id, source_project['runbiosimulationsId'], reason))

        # print message
        if errors:
            msg = '{} projects have been successfully published.\n\n'.format(len(source_projects) - len(errors))
            msg += '{} projects have not been successfully published:\n  {}'.format(len(errors), '\n  '.join(errors))
            raise SystemExit(msg)

        else:
            print('All {} projects have been successfully published.'.format(len(source_projects)))


class App(cement.App):
    """ Command line application """
    class Meta:
        label = 'biosimulations-modeldb'
        base_controller = 'base'
        handlers = [
            BaseController,
            RunAndPublishProjectsController,
            PublishRunsController,
            VerifyPublicationController,
        ]


def main():
    with App() as app:
        app.run()
