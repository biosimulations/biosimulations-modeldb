from biosimulations_modeldb import __main__
from biosimulations_modeldb._version import __version__
from biosimulations_modeldb.core import (
    get_project_ids, get_project, get_paper_metadata,
    get_metadata_for_project,
    export_project_metadata_for_project_to_omex_metadata,
    init_combine_archive_from_dir,
    create_sedml_for_xpp_file,
    build_combine_archive_for_project,
    make_directories,
    import_project, import_projects,
    TAXA,
    ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY,
)
from biosimulations_modeldb.config import get_config
from biosimulators_utils.combine.data_model import CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveReader
from biosimulators_utils.omex_meta.io import BiosimulationsOmexMetaReader
from biosimulators_utils.ref.data_model import JournalArticle
from biosimulators_utils.sedml.io import SedmlSimulationWriter, SedmlSimulationReader
from biosimulators_utils.sedml.validation import validate_doc
from unittest import mock
import Bio.Entrez
import biosimulations_modeldb.__main__
import capturer
import git
import os
import requests
import requests_cache
import shutil
import tempfile
import unittest

Bio.Entrez.email = 'biosimulations.daemon@gmail.com'


class MockCrossRefSessionResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            'message': {
                'title': [''],
                'container-title': [''],
                'volume': '',
                'published': {
                    'date-parts': [
                        [
                            2021,
                            12,
                            31,
                        ]
                    ]
                }
            }
        }


class MockCrossRefSession:
    def get(self, url):
        return MockCrossRefSessionResponse()


class MockS3Bucket:
    def __init__(self, name):
        pass

    def upload_file(self, *args, **kwargs):
        pass


class TestCase(unittest.TestCase):
    def setUp(self):
        self.case_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.case_dirname)

    @classmethod
    def setUpClass(cls):
        cls.dirname = tempfile.mkdtemp()
        git.Repo.init(cls.dirname)
        cls.pkg_dirname = os.path.join(cls.dirname, 'biosimulations_modeldb')
        os.mkdir(cls.pkg_dirname)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dirname)

    def test_get_project_ids(self):
        config = get_config(
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
        )
        ids = get_project_ids(config, 'XPP')
        self.assertIn(35358, ids)
        self.assertGreater(len(ids), 100)

    def test_get_paper_metadata(self):
        config = get_config(
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
        )
        paper = {
            'object_id': 5225,
        }
        get_paper_metadata(paper, config)
        self.assertEqual(paper, {
            'object_id': 5225,
            'uris': {
                'doi': None,
                'pubmed': '8792224',
                'url': None,
            },
            'citation': paper['citation'],
        })
        self.assertEqual(paper['citation'].authors, ['Pinsky PF', 'Rinzel J'])
        self.assertEqual(paper['citation'].title, 'Intrinsic and network rhythmogenesis in a reduced Traub model for CA3 neurons')
        self.assertEqual(paper['citation'].journal, 'J Comput Neurosci')
        self.assertEqual(paper['citation'].volume, '1')
        self.assertEqual(paper['citation'].issue, None)
        self.assertEqual(paper['citation'].pages, '39-60')
        self.assertEqual(paper['citation'].year, 1994)

    def test_get_paper_metadata_without_pages(self):
        config = get_config(
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
        )

        def json():
            return {
                'title': {'value': 'XYZ'},
                'authors': {'value': [{'object_name': 'abc'}]},
                'journal': {'value': 'def'},
                'year': {'value': 2022},
            }

        def get(url):
            return mock.Mock(
                raise_for_status=lambda: None,
                json=json,
            )

        config['source_session'] = mock.Mock(
            get=get
        )
        paper = {
            'object_id': 186225,
        }
        get_paper_metadata(paper, config)
        self.assertEqual(paper, {
            'object_id': 186225,
            'uris': {
                'doi': None,
                'pubmed': None,
                'url': None,
            },
            'citation': paper['citation'],
        })
        self.assertEqual(paper['citation'].authors, ['abc'])
        self.assertEqual(paper['citation'].title, 'XYZ')
        self.assertEqual(paper['citation'].journal, 'def')
        self.assertEqual(paper['citation'].volume, None)
        self.assertEqual(paper['citation'].issue, None)
        self.assertEqual(paper['citation'].pages, None)
        self.assertEqual(paper['citation'].year, 2022)

    def test_get_paper_metadata_with_pages(self):
        config = get_config(
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
        )

        def json():
            return {
                'title': {'value': 'XYZ'},
                'authors': {'value': [{'object_name': 'abc'}]},
                'journal': {'value': 'def'},
                'volume': {'value': 'ghi'},
                'first_page': {'value': '1'},
                'last_page': {'value': '2'},
                'year': {'value': 2022},
                'doi': {'value': 'jkl'},
                'pubmed_id': {'value': 'mno'},
                'url': {'value': 'pqr'},
            }

        def get(url):
            return mock.Mock(
                raise_for_status=lambda: None,
                json=json,
            )

        config['source_session'] = mock.Mock(
            get=get
        )
        paper = {
            'object_id': 186225,
        }
        get_paper_metadata(paper, config)
        self.assertEqual(paper, {
            'object_id': 186225,
            'uris': {
                'doi': 'jkl',
                'pubmed': 'mno',
                'url': 'pqr',
            },
            'citation': paper['citation'],
        })
        self.assertEqual(paper['citation'].authors, ['abc'])
        self.assertEqual(paper['citation'].title, 'XYZ')
        self.assertEqual(paper['citation'].journal, 'def')
        self.assertEqual(paper['citation'].volume, 'ghi')
        self.assertEqual(paper['citation'].issue, None)
        self.assertEqual(paper['citation'].pages, '1-2')
        self.assertEqual(paper['citation'].year, 2022)

    def test_get_project(self):
        config = get_config(
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
        )
        project = get_project(35358, config)
        self.assertEqual(project['id'], 35358)
        self.assertEqual(project['name'], 'CA3 pyramidal cell: rhythmogenesis in a reduced Traub model (Pinsky, Rinzel 1994)')
        self.assertEqual(project['created'], '2004-02-09T17:12:24')

    def test_get_metadata_for_project(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 136097,
            'species': {
                'value': [{'object_name': 'Drosophila'}],
            },
            'region': {
                'value': [{'object_name': 'Auditory brainstem'}],
            },
            'model_paper': {
                'value': [{
                    'object_id': 136105,
                    'uris': {
                        'doi': '10.1093/chemse/bjp032',
                        'pubmed': None,
                        'url': None,
                    },
                    'citation': JournalArticle(),
                }],
            },
        }
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '136097'), config)

        self.assertTrue(description.startswith('This is the readme for the model associated with the AChems abstract'))
        self.assertEqual(taxa, [{'uri': 'http://identifiers.org/taxonomy:7215', 'label': 'Drosophila'}])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1093/chemse/bjp032')
        self.assertTrue(references[0]['label'].startswith('Abstracts from the Thirty-first Annual Meeting'))
        self.assertEqual(thumbnails, [])

        # read from cache
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '136097'), config)

        self.assertTrue(description.startswith('This is the readme for the model associated with the AChems abstract'))
        self.assertEqual(taxa, [{'uri': 'http://identifiers.org/taxonomy:7215', 'label': 'Drosophila'}])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1093/chemse/bjp032')
        self.assertTrue(references[0]['label'].startswith('Abstracts from the Thirty-first Annual Meeting'))
        self.assertEqual(thumbnails, [])

    def test_get_metadata_for_project_no_description(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 58712,
            'region': {
                'value': [{'object_name': 'Drosophila'}],
            }
        }

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '58712'), config)
        self.assertEqual(description, None)
        self.assertEqual(taxa, [{'uri': 'http://identifiers.org/taxonomy:7215', 'label': 'Drosophila'}])

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '58712'), config)
        self.assertEqual(description, None)
        self.assertEqual(taxa, [{'uri': 'http://identifiers.org/taxonomy:7215', 'label': 'Drosophila'}])

    def test_get_metadata_for_project_no_annotated_taxonomy(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 57910,
            'species': {
                'value': [{'object_name': 'Escherichia coli'}],
            }
        }

        with self.assertRaisesRegex(ValueError, 'Taxonomy must be annotated'):
            description, taxa, references, thumbnails = get_metadata_for_project(
                project, os.path.join(config['source_projects_dirname'], '57910'), config)

    def test_get_metadata_for_project_with_images(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 57910,
            'model_paper': {
                'value': [{
                    'object_id': 57915,
                    'uris': {
                        'doi': None,
                        'pubmed': '9192303',
                        'url': None,
                    },
                    'citation': JournalArticle(),
                }],
            },
        }
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '57910'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the model associated with the paper'))
        self.assertEqual(taxa, [])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1111/j.1469-7793.1997.313bn.x')
        self.assertTrue(references[0]['label'].startswith('Nicoletta Chiesa,'))
        self.assertEqual(thumbnails, [{
            'local_filename': os.path.join(config['source_projects_dirname'], '57910', 'samplerun.jpg'),
            'archive_filename': 'samplerun.jpg',
            'format': 'jpeg',
        }])

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '57910'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the model associated with the paper'))
        self.assertEqual(taxa, [])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1111/j.1469-7793.1997.313bn.x')
        self.assertTrue(references[0]['label'].startswith('Nicoletta Chiesa,'))
        self.assertEqual(thumbnails, [{
            'local_filename': os.path.normpath(os.path.join(config['source_projects_dirname'], '57910', 'samplerun.jpg')),
            'archive_filename': 'samplerun.jpg',
            'format': 'jpeg',
        }])

    def test_get_metadata_for_project_no_doi_pubmed(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 76879,
            'model_paper': {
                'value': [{
                    'object_id': 57915,
                    'uris': {
                        'doi': None,
                        'pubmed': None,
                        'url': 'http://example.com',
                    },
                    'citation': JournalArticle(title='Example'),
                }],
            },
        }
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '76879'), config)
        self.assertTrue(description.startswith('From Excitatory and Inhibitory Interactions in'))
        self.assertEqual(taxa, [])
        self.assertEqual(references, [{
            'uri': 'http://example.com',
            'label': 'Example.',
        }])
        self.assertEqual(thumbnails, [])

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '76879'), config)
        self.assertTrue(description.startswith('From Excitatory and Inhibitory Interactions in'))
        self.assertEqual(taxa, [])
        self.assertEqual(references, [{
            'uri': 'http://example.com',
            'label': 'Example.',
        }])
        self.assertEqual(thumbnails, [])

    def test_get_metadata_for_project_no_citations(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 45513,
        }
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '45513'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the models associated with the paper'))
        self.assertEqual(taxa, [])
        self.assertEqual(references, [])
        self.assertEqual(thumbnails, [])

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '45513'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the models associated with the paper'))
        self.assertEqual(taxa, [])
        self.assertEqual(references, [])
        self.assertEqual(thumbnails, [])

    def test_get_metadata_for_project_with_pmc_images(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 83558,
            'model_paper': {
                'value': [{
                    'object_id': 1234,
                    'uris': {
                        'doi': None,
                        'pubmed': '16965177',
                        'url': None,
                    },
                    'citation': JournalArticle(),
                }],
            },
        }
        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '83558'), config)
        self.assertTrue(description.startswith('This is the readme for the model code associated with the publication:'))
        self.assertEqual(taxa, [])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1371/journal.pcbi.0020119')
        self.assertTrue(references[0]['label'].startswith('Maria Lindskog,'))
        self.assertEqual(thumbnails[0]['id'], 'pcbi.0020119/pcbi-0020119-g001')
        self.assertEqual(thumbnails[0]['local_filename'], os.path.join(
            config['source_thumbnails_dirname'], 'PMC1562452', 'PMC1562452', 'pcbi.0020119.g001.jpg'))
        self.assertEqual(thumbnails[0]['archive_filename'], os.path.join(
            ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY, 'PMC1562452', 'pcbi.0020119.g001.jpg'))
        self.assertEqual(thumbnails[0]['format'], 'jpeg')
        self.assertEqual(thumbnails[0]['label'], 'Figure 1')
        self.assertTrue(thumbnails[0]['caption'].startswith('<title '))

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '83558'), config)
        self.assertTrue(description.startswith('This is the readme for the model code associated with the publication:'))
        self.assertEqual(taxa, [])
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/doi:10.1371/journal.pcbi.0020119')
        self.assertTrue(references[0]['label'].startswith('Maria Lindskog,'))
        self.assertEqual(thumbnails[0]['id'], 'pcbi.0020119/pcbi-0020119-g001')
        self.assertEqual(thumbnails[0]['local_filename'], os.path.join(
            config['source_thumbnails_dirname'], 'PMC1562452', 'PMC1562452', 'pcbi.0020119.g001.jpg'))
        self.assertEqual(thumbnails[0]['archive_filename'], os.path.join(
            ARTICLE_FIGURES_COMBINE_ARCHIVE_SUBDIRECTORY, 'PMC1562452', 'pcbi.0020119.g001.jpg'))
        self.assertEqual(thumbnails[0]['format'], 'jpeg')
        self.assertEqual(thumbnails[0]['label'], 'Figure 1')
        self.assertTrue(thumbnails[0]['caption'].startswith('<title '))

    def test_get_metadata_for_project_without_doi(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 64171,
            'model_paper': {
                'value': [{
                    'object_id': 55860,
                    'uris': {
                        'doi': None,
                        'pubmed': '15239590',
                        'url': None,
                    },
                    'citation': JournalArticle(),
                }],
            },
        }

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '64171'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the models associated with the paper'))
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/pubmed:15239590')
        self.assertTrue(references[0]['label'].startswith('Wu SN.'))

        description, taxa, references, thumbnails = get_metadata_for_project(
            project, os.path.join(config['source_projects_dirname'], '64171'), config)
        self.assertTrue(description.startswith('This is the readme.txt for the models associated with the paper'))
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['uri'], 'http://identifiers.org/pubmed:15239590')
        self.assertTrue(references[0]['label'].startswith('Wu SN.'))

    def test_export_project_metadata_for_project_to_omex_metadata(self):
        base_config = get_config()
        config = get_config(
            base_dirname=self.pkg_dirname,
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
        )
        config['source_projects_dirname'] = base_config['source_projects_dirname']
        if not os.path.isdir(config['source_thumbnails_dirname']):
            os.makedirs(config['source_thumbnails_dirname'])
        if not os.path.isdir(os.path.join(config['final_metadata_dirname'])):
            os.makedirs(os.path.join(config['final_metadata_dirname']))

        project = {
            'id': 57910,
            'name': 'abc',
            'notes': {
                'value': 'def',
            },
            'model_type': {
                'value': [{
                    'object_id': '123',
                    'object_name': 'My model type',
                }]
            },
            'region': {
                'value': [
                    {
                        'object_id': '456',
                        'object_name': 'Generic',
                    },
                    {
                        'object_id': '789',
                        'object_name': 'My region (xyz)',
                    },
                ]
            },
            'other_type': {
                'value': 'My other type',
            },
            'implemented_by': {
                'value': [
                    {
                        'object_name': 'Jane Doe [email at domain]',
                    },
                    {
                        'object_name': 'Jack Doer',
                    },
                ],
            },
            'public_submitter_name': {
                'value': 'John Doe'
            },
            'public_submitter_email': {
                'value': 'email2@domain',
            },
            'created': '2022-01-01',
            'ver_date': '2022-01-02',
        }
        description = 'ghi'
        taxa = [{
            'uri': 'http://identifiers.org/taxonomy:7215',
            'label': 'Drosophila',
        }]
        references = [{
            'uri': 'http://identifiers.org/doi:10.1093/chemse/bjp032',
            'label': 'jkl',
        }]
        thumbnails = [{
            'local_filename': os.path.join(config['source_projects_dirname'], '57910', 'samplerun.jpg'),
            'archive_filename': './samplerun.jpg',
            'format': 'jpeg',
        }]
        metadata_filename = os.path.join(self.case_dirname, 'metadata.rdf')
        export_project_metadata_for_project_to_omex_metadata(project, description, taxa, references, thumbnails, metadata_filename, config)

        metadata, errors, warnings = BiosimulationsOmexMetaReader().run(
            metadata_filename, working_dir=os.path.join(config['source_projects_dirname'], '57910'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        expected_metadata = {
            "uri": '.',
            "combine_archive_uri": 'http://omex-library.org/57910.omex',
            'title': 'abc',
            'abstract': 'def',
            'keywords': [],
            'description': 'ghi',
            'taxa': taxa,
            'encodes': [
                {
                    'uri': 'http://modeldb.science/ModelList?id=123',
                    'label': 'My model type',
                },
                {
                    'uri': None,
                    'label': 'My other type',
                },
                {
                    'uri': 'http://modeldb.science/ModelList?id=789',
                    'label': 'My region',
                },
            ],
            'thumbnails': [
                thumbnail['archive_filename']
                for thumbnail in thumbnails
            ],
            'sources': [],
            'predecessors': [],
            'successors': [],
            'see_also': [],
            'creators': [
                {
                    'uri': 'mailto:email@domain',
                    'label': 'Jane Doe',
                },
                {
                    'uri': None,
                    'label': 'Jack Doer',
                },
            ],
            'contributors': [
                {
                    'uri': 'mailto:email2@domain',
                    'label': 'John Doe',
                },
                {
                    'uri': 'https://senselab.med.yale.edu/',
                    'label': 'Sense Lab at Yale University',
                },
                {
                    'uri': 'http://identifiers.org/orcid:0000-0002-2605-5080',
                    'label': 'Jonathan R. Karr',
                },
            ],
            'identifiers': [
                {
                    'uri': 'https://identifiers.org/modeldb:57910',
                    'label': 'modeldb:57910',
                },
            ],
            'citations': references,
            'references': [],
            'license': None,
            'funders': [],
            'created': '2022-01-01',
            'modified': [
                '2022-01-02',
            ],
            'other': [],
        }
        self.assertEqual(metadata, [expected_metadata])

        with self.assertRaisesRegex(ValueError, 'metadata is not valid'):
            with mock.patch.object(BiosimulationsOmexMetaReader, 'run', return_value=[None, [['My error']], []]):
                export_project_metadata_for_project_to_omex_metadata(
                    project, description, taxa, references, thumbnails, metadata_filename, config)

    def test_init_combine_archive_from_dir(self):
        config = get_config()
        dirname = os.path.join(config['source_projects_dirname'], '57910')
        init_combine_archive_from_dir(dirname)

        with open(os.path.join(self.case_dirname, 'test1.unknown'), 'w') as file:
            file.write('here')
        with open(os.path.join(self.case_dirname, 'test2.xml'), 'w') as file:
            file.write('<sbml xmlns="http://www.sbml.org/sbml/"></sbml>')
        with open(os.path.join(self.case_dirname, 'test3.xml'), 'w') as file:
            file.write('<nml xmlns="http://morphml.org/neuroml/schema"></nml>')
        with open(os.path.join(self.case_dirname, 'test4.xml'), 'w') as file:
            file.write('<xml></xml>')
        with open(os.path.join(self.case_dirname, 'test5.xml'), 'w') as file:
            file.write('<xml></xml')
        with open(os.path.join(self.case_dirname, 'test6.jpg'), 'w') as file:
            file.write('here')
        with open(os.path.join(self.case_dirname, 'desktop.ini'), 'w') as file:
            file.write('here')
        with self.assertWarnsRegex(UserWarning, 'is not known'):
            archive = init_combine_archive_from_dir(self.case_dirname)
        archive.contents.sort(key=lambda content: content.location)
        self.assertEqual(len(archive.contents), 5)
        self.assertEqual(archive.contents[0].location, 'test1.unknown')
        self.assertEqual(archive.contents[0].format, CombineArchiveContentFormat.OTHER.value)
        self.assertEqual(archive.contents[1].location, 'test2.xml')
        self.assertEqual(archive.contents[1].format, CombineArchiveContentFormat.SBML.value)
        self.assertEqual(archive.contents[2].location, 'test3.xml')
        self.assertEqual(archive.contents[2].format, CombineArchiveContentFormat.NeuroML.value)
        self.assertEqual(archive.contents[3].location, 'test4.xml')
        self.assertEqual(archive.contents[3].format, CombineArchiveContentFormat.XML.value)
        self.assertEqual(archive.contents[4].location, 'test5.xml')
        self.assertEqual(archive.contents[4].format, CombineArchiveContentFormat.OTHER.value)

    def test_create_sedml_for_xpp_file(self):
        config = get_config()

        dirname = os.path.join(config['source_projects_dirname'], '35358')
        sed_doc = create_sedml_for_xpp_file(35358, dirname, 'booth_bose.ode')

        sedml_filename = os.path.join(dirname, '_test_.sedml')
        SedmlSimulationWriter().run(sed_doc, sedml_filename)
        sed_doc_2 = SedmlSimulationReader().run(sedml_filename)
        os.remove(sedml_filename)

        # SedmlSimulationWriter().run(sed_doc, 'test.sedml',
        #                             validate_semantics=False,
        #                             validate_models_with_languages=False,
        #                             validate_targets_with_model_sources=False)

        errors, warnings = validate_doc(sed_doc, dirname)
        self.assertEqual(errors, [])

    def test_create_sedml_for_xpp_file_with_set_file(self):
        config = get_config()

        dirname = os.path.join(config['source_projects_dirname'], '116867')
        sed_doc = create_sedml_for_xpp_file(116867, dirname, 'rubin_terman_pd.ode')

        sedml_filename = os.path.join(dirname, '_test_.sedml')
        SedmlSimulationWriter().run(sed_doc, sedml_filename)
        sed_doc_2 = SedmlSimulationReader().run(sedml_filename)
        os.remove(sedml_filename)

        # SedmlSimulationWriter().run(sed_doc, 'test.sedml',
        #                             validate_semantics=False,
        #                             validate_models_with_languages=False,
        #                             validate_targets_with_model_sources=False)

        errors, warnings = validate_doc(sed_doc, dirname)
        self.assertEqual(errors, [])

    def test_build_combine_archive_for_project(self):
        config = get_config()

        id = 57910
        source_project_dirname = os.path.join(config['source_projects_dirname'], '57910')
        final_project_dirname = os.path.join(self.case_dirname, 'archive')
        archive_filename = os.path.join(self.case_dirname, 'archive.omex')
        extra_contents = {
            os.path.join(config['source_projects_dirname'], '57910', 'samplerun.jpg'): CombineArchiveContent(
                location='samplerun.jpg',
                format=CombineArchiveContentFormat.JPEG.value,
            ),
            'MANIFEST.in': CombineArchiveContent(
                location='MANIFEST.in',
                format=CombineArchiveContentFormat.TEXT.value,
            ),
        }
        build_combine_archive_for_project(id, source_project_dirname, final_project_dirname, archive_filename, extra_contents)

        archive_dirname = os.path.join(self.case_dirname, 'unpacked')
        archive = CombineArchiveReader().run(archive_filename, archive_dirname)

    def test_build_combine_archive_for_project_extra_content_in_sub_dir(self):
        config = get_config()

        id = 57910
        source_project_dirname = os.path.join(config['source_projects_dirname'], '57910')
        final_project_dirname = os.path.join(self.case_dirname, 'archive')
        archive_filename = os.path.join(self.case_dirname, 'archive.omex')
        extra_contents = {
            os.path.join(config['source_projects_dirname'], '57910', 'samplerun.jpg'): CombineArchiveContent(
                location=os.path.join('subdir', 'samplerun.jpg'),
                format=CombineArchiveContentFormat.JPEG.value,
            ),
            'MANIFEST.in': CombineArchiveContent(
                location='MANIFEST.in',
                format=CombineArchiveContentFormat.TEXT.value,
            ),
        }
        build_combine_archive_for_project(id, source_project_dirname, final_project_dirname, archive_filename, extra_contents)

        archive_dirname = os.path.join(self.case_dirname, 'unpacked')
        archive = CombineArchiveReader().run(archive_filename, archive_dirname)
        self.assertTrue(os.path.isfile(os.path.join(archive_dirname, 'subdir', 'samplerun.jpg')))

    def test_import_project(self):
        base_config = get_config()

        config = get_config(
            base_dirname=self.pkg_dirname,
            source_dirname=os.path.join(self.pkg_dirname, 'source'),
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
            issues_filename=base_config['issues_filename'],
            status_filename=os.path.join(self.pkg_dirname, 'final', 'status.yml'),
            max_projects=1,
            bucket_name='bucket',
        )
        make_directories(config)

        config['cross_ref_session'] = MockCrossRefSession()

        project = get_project(57910, config)
        auth = ''

        with mock.patch('biosimulators_utils.biosimulations.utils.run_simulation_project', return_value='*' * 32):
            with mock.patch('boto3.resource', return_value=mock.Mock(Bucket=MockS3Bucket)):
                import_project(project, True, auth, config)

    def test_import_projects(self):
        base_config = get_config()

        config = get_config(
            base_dirname=self.pkg_dirname,
            source_dirname=os.path.join(self.pkg_dirname, 'source'),
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
            issues_filename=base_config['issues_filename'],
            status_filename=os.path.join(self.pkg_dirname, 'final', 'status.yml'),
            max_projects=1,
            bucket_name='bucket',
        )

        config['cross_ref_session'] = MockCrossRefSession()

        with mock.patch('biosimulators_utils.biosimulations.utils.run_simulation_project', return_value='*' * 32):
            with mock.patch('biosimulators_utils.biosimulations.utils.get_authorization_for_client', return_value='xxx yyy'):
                with mock.patch('boto3.resource', return_value=mock.Mock(Bucket=MockS3Bucket)):
                    import_projects(config)

    def test_import_projects_dry_run(self):
        base_config = get_config()

        config = get_config(
            base_dirname=self.pkg_dirname,
            source_dirname=os.path.join(self.pkg_dirname, 'source'),
            sessions_dirname=os.path.join(self.pkg_dirname, 'source'),
            final_dirname=os.path.join(self.pkg_dirname, 'final'),
            curators_filename=base_config['curators_filename'],
            issues_filename=base_config['issues_filename'],
            status_filename=os.path.join(self.pkg_dirname, 'final', 'status.yml'),
            max_projects=1,
            bucket_name='bucket',
        )

        config['cross_ref_session'] = MockCrossRefSession()
        config['dry_run'] = True
        config['simulate_projects'] = False
        config['publish_projects'] = False

        with mock.patch('biosimulators_utils.biosimulations.utils.get_authorization_for_client', return_value='xxx yyy'):
            with mock.patch('boto3.resource', return_value=mock.Mock(Bucket=MockS3Bucket)):
                import_projects(config)

    def test_cli(self):
        base_config = get_config()

        with mock.patch.dict('os.environ', {
            'BASE_DIRNAME': self.pkg_dirname,
            'SOURCE_DIRNAME': os.path.join(self.pkg_dirname, 'source'),
            'SESSIONS_DIRNAME': os.path.join(self.pkg_dirname, 'source'),
            'FINAL_DIRNAME': os.path.join(self.pkg_dirname, 'final'),
            'CURATORS_FILENAME': base_config['curators_filename'],
            'ISSUES_FILENAME': base_config['issues_filename'],
            'STATUS_FILENAME': os.path.join(self.pkg_dirname, 'final', 'status.yml'),
            'BUCKET_NAME': 'bucket',
        }):
            def mock_get_config(**args):
                config = get_config(**args)
                config['cross_ref_session'] = MockCrossRefSession()
                return config

            with mock.patch('biosimulators_utils.biosimulations.utils.run_simulation_project', return_value='*' * 32):
                with mock.patch('biosimulators_utils.biosimulations.utils.get_authorization_for_client', return_value='xxx yyy'):
                    with mock.patch('boto3.resource', return_value=mock.Mock(Bucket=MockS3Bucket)):
                        import biosimulations_modeldb.config
                        with mock.patch.object(biosimulations_modeldb.__main__, 'get_config', side_effect=mock_get_config):
                            with __main__.App(argv=[
                                'run-projects-and-publish',
                                '--max-projects', '1',
                            ]) as app:
                                app.run()

    def test_cli_help(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit):
                __main__.main()

    def test_version(self):
        with __main__.App(argv=['--version']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertEqual(stdout, __version__)
                self.assertEqual(captured.stderr.get_text(), '')
