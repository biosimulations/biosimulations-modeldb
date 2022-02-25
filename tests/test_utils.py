from biosimulations_modeldb.utils import (get_file_extension_combine_uri_map, case_insensitive_glob, get_readme, get_images_for_project)
from biosimulators_utils.combine.data_model import CombineArchiveContentFormat
import unittest


class UtilsTestCase(unittest.TestCase):
    def test_get_file_extension_combine_uri_map(self):
        map = get_file_extension_combine_uri_map()
        self.assertEqual(map['png'], CombineArchiveContentFormat.PNG.value)

    def test_case_insensitive_glob(self):
        self.assertNotEqual(case_insensitive_glob('*.md'), [])
        self.assertEqual(case_insensitive_glob('*.md'), case_insensitive_glob('*.MD'))

    def test_get_text_readme(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/136097/readme.txt',
            136097,
            'biosimulations_modeldb/source/projects/136097',
        )
        self.assertTrue(readme.startswith('This is the readme for'))

    def test_get_markdown_readme(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/206364/README.md',
            206364,
            'biosimulations_modeldb/source/projects/206364',
        )
        self.assertTrue(readme.startswith('# ISR-of-Purkinje-cells'))

    def test_get_html_preformatted_readme(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/105528/readme.html',
            105528,
            'biosimulations_modeldb/source/projects/105528',
        )
        self.assertTrue(readme.startswith('This is the readme.txt'))

        self.assertIn('![screenshot](data:image/jpeg;base64,', readme)

    def test_get_html_not_preformatted_readme(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/260730/readme.html',
            260730,
            'biosimulations_modeldb/source/projects/260730',
        )
        self.assertTrue(readme.startswith('This is the readme for the models associated with the paper:\n\n\n Sherman AS, Ha J'))

        self.assertIn('![screenshot](data:image/png;base64,', readme)
        self.assertIn('```\n\nxppaut ML.ode\n\n```', readme)

    def test_get_html_readme_with_incorrect_image_filename(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/84606/readme.html',
            84606,
            'biosimulations_modeldb/source/projects/84606',
        )
        self.assertTrue(readme.startswith('This is the readme.txt'))

        self.assertIn('![ZNS_graph.jpg](data:image/jpeg;base64,', readme)

    def test_get_docx_readme(self):
        readme = get_readme(
            'biosimulations_modeldb/source/projects/152113/readme.docx',
            152113,
            'biosimulations_modeldb/source/projects/152113',
        )
        self.assertTrue(readme.startswith('This archive contains MATLAB codes'))

        self.assertRegex(readme, r'!\[D:\\.*?\\Paper_DualCon_final\\ChenEtAl2014_final\\screenshot\.png\]\(data:image/png;base64,')

    def test_get_readme_error_handling(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            get_readme(
                'MANIFEST.in',
                None,
                './',
            )

    def test_get_images_for_project(self):
        self.assertEqual(set(get_images_for_project('biosimulations_modeldb/source/projects/142630')),
                         set([
                             'biosimulations_modeldb/source/projects/142630/fig4A.jpg',
                             'biosimulations_modeldb/source/projects/142630/fig4B.jpg',
                             'biosimulations_modeldb/source/projects/142630/fig4C.jpg',
                             'biosimulations_modeldb/source/projects/142630/fig4D.jpg',
                         ]))
