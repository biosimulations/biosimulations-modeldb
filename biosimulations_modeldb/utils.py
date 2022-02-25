from biosimulators_utils.biosimulations.utils import get_file_extension_combine_uri_map as base_get_file_extension_combine_uri_map
from biosimulators_utils.combine.data_model import CombineArchiveContentFormat
import base64
import bs4
import glob
import imghdr
import mammoth
import markdownify
import os
import warnings

__all__ = [
    'get_file_extension_combine_uri_map',
    'case_insensitive_glob',
    'get_readme',
    'get_images_for_project',
]


def get_file_extension_combine_uri_map():
    """ Get a map from file extensions to URIs for use with manifests of COMBINE/OMEX archives

    Args:
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`dict`: which maps extensions to lists of associated URIs
    """
    map = base_get_file_extension_combine_uri_map()

    map['ac'] = {'http://purl.org/NET/mediatypes/text/x-autoconf'}
    map['auto'] = {CombineArchiveContentFormat.XPP_AUTO.value}
    map['cc'] = map['cpp']
    map['dist'] = {CombineArchiveContentFormat.MARKDOWN.value}
    map['eps'] = {CombineArchiveContentFormat.POSTSCRIPT.value}
    map['fig'] = {CombineArchiveContentFormat.MATLAB_FIGURE.value}
    map['g'] = {CombineArchiveContentFormat.GENESIS.value}
    map['hoc'] = {CombineArchiveContentFormat.HOC.value}
    map['html'] = {CombineArchiveContentFormat.HTML.value}
    map['in'] = {CombineArchiveContentFormat.NCS.value}
    map['inc'] = {CombineArchiveContentFormat.NMODL.value}
    map['map'] = {CombineArchiveContentFormat.TSV.value}
    map['md'] = {CombineArchiveContentFormat.MARKDOWN.value}
    map['mlx'] = {'http://purl.org/NET/mediatypes/application/matlab-live-script'}
    map['mod'] = {CombineArchiveContentFormat.NMODL.value}
    map['mw'] = {CombineArchiveContentFormat.MAPLE_WORKSHEET.value}
    map['nb'] = {CombineArchiveContentFormat.MATHEMATICA_NOTEBOOK.value}
    map['nrn'] = {CombineArchiveContentFormat.HOC.value}
    map['ode'] = {CombineArchiveContentFormat.XPP.value}
    map['p'] = {CombineArchiveContentFormat.GENESIS.value}
    map['pdf'] = {CombineArchiveContentFormat.PDF.value}
    map['ps'] = {CombineArchiveContentFormat.POSTSCRIPT.value}
    map['sce'] = {CombineArchiveContentFormat.Scilab.value}
    map['ses'] = {CombineArchiveContentFormat.NEURON_SESSION.value}
    map['set'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['sfit'] = {CombineArchiveContentFormat.MATLAB_DATA.value}
    map['sli'] = {CombineArchiveContentFormat.SLI.value}
    map['tab'] = {CombineArchiveContentFormat.TSV.value}
    map['txt'] = {CombineArchiveContentFormat.TEXT.value}
    map['xls'] = {CombineArchiveContentFormat.XLS.value}
    map['xpp'] = {CombineArchiveContentFormat.XPP.value}

    map['inp'] = {CombineArchiveContentFormat.TEXT.value}

    map[''] = {CombineArchiveContentFormat.OTHER.value}
    map['bin'] = {CombineArchiveContentFormat.OTHER.value}
    map['dat'] = {CombineArchiveContentFormat.OTHER.value}
    map['mexmaci64'] = {CombineArchiveContentFormat.OTHER.value}
    map['mexw64'] = {CombineArchiveContentFormat.OTHER.value}
    map['mexa64'] = {CombineArchiveContentFormat.OTHER.value}

    map['set3'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['setdb'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['setnorm'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['setpark'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['setsb'] = {CombineArchiveContentFormat.XPP_SET.value}
    map['setsdb'] = {CombineArchiveContentFormat.XPP_SET.value}

    for ext, uris in map.items():
        if len(uris) > 1:
            msg = 'URI for extension `{}` could not be uniquely determined:\n  {}'.format(
                ext, '\n  '.join(sorted(uris)))
            warnings.warn(msg, UserWarning)

        if uris:
            map[ext] = list(uris)[0]
        else:
            map[ext] = CombineArchiveContentFormat.OTHER.value

    return map


def case_insensitive_glob(pattern, **kwargs):
    """ Glob without case sensitivity

    Args:
        pattern (:obj:`str`): glob pattern
        **kwargs

    Returns:
        :obj:`list` of :obj:`str`: path of files that match the glob pattern
    """
    def either(c):
        if c.isalpha():
            return '[{}{}]'.format(c.lower(), c.upper())
        else:
            return c
    return glob.glob(''.join(map(either, pattern)), **kwargs)


def get_images_for_project(dirname):
    """ Get the images for a project

    Args:
        dirname (:obj:`str`): directory for project

    Returns:
        :obj:`list` of :obj:`str`: paths to the images
    """
    return (
        case_insensitive_glob(os.path.join(dirname, '**', '*.gif'), recursive=True)
        + case_insensitive_glob(os.path.join(dirname, '**', '*.jpeg'), recursive=True)
        + case_insensitive_glob(os.path.join(dirname, '**', '*.jpg'), recursive=True)
        + case_insensitive_glob(os.path.join(dirname, '**', '*.png'), recursive=True)
        + case_insensitive_glob(os.path.join(dirname, '**', '*.webp'), recursive=True)
    )


def get_readme(filename, project_id, project_dirname):
    """ Read the content of a README file

    Args:
        filename (:obj:`str`): path to README file
        project_id (:obj:`str`): project id
        project_dirname (:obj:`str`): project directory

    Returns:
        :obj:`str`: Markdown-formatted content of the file
    """
    _, ext = os.path.splitext(filename.lower())
    if ext in ['', '.txt', '.md']:
        with open(filename, 'r') as file:
            return file.read().strip()

    elif ext in ['.html']:
        with open(filename, 'rb') as file:
            doc = bs4.BeautifulSoup(file.read(), features='lxml')
        content = doc.find('body') or doc

        content_all_pre = True
        for child in content.children:
            if isinstance(child, bs4.element.Tag) and child.name != 'pre':
                content_all_pre = False
                break

        if content_all_pre:
            new_container = bs4.BeautifulSoup('<div></div>', features='lxml').div
            pre = content.find('pre')
            pre.insert_after(new_container)
            for child in list(pre.children):
                new_container.append(child.extract())
            pre.decompose()

        image_work_dirname = os.path.dirname(filename)

        project_image_filename_map = {}
        for project_image_filename in get_images_for_project(project_dirname):
            basename, ext = os.path.splitext(os.path.relpath(project_image_filename, project_dirname))
            project_image_filename_map[basename.lower() + ext.lower()] = project_image_filename

        for image_el in content.find_all('img'):
            image_src_html = os.path.join(image_work_dirname, os.path.relpath(image_el.get('src'), '.'))
            image_basename, image_ext = os.path.splitext(os.path.relpath(image_src_html, project_dirname))
            image_src = project_image_filename_map.get(image_basename.lower() + image_ext.lower(), None)
            if image_src != image_src_html:
                warnings.warn((
                    f'Image source `{image_el.get("src")}` '
                    f'in readme `{os.path.relpath(filename, project_dirname)}` '
                    f'for project `{project_id}` is incorrect'
                ), UserWarning)

            image_format = imghdr.what(image_src)
            with open(image_src, 'rb') as image_file:
                image_value = base64.b64encode(image_file.read()).decode()
                image_el['src'] = f'data:image/{image_format};base64,{image_value}'

            parent_el = image_el.parent
            if parent_el.name == 'pre':
                sibling_els = list(parent_el.children)
                i_image = sibling_els.index(image_el)

                below_container = bs4.BeautifulSoup('<pre></pre>', features='lxml').pre
                parent_el.insert_after(below_container)
                for sibling_el in sibling_els[i_image + 1:]:
                    below_container.append(sibling_el)

                parent_el.insert_after(image_el)

        return markdownify.MarkdownConverter().convert_soup(content).strip()

    elif ext in ['.docx']:
        with open(filename, 'rb') as file:
            result = mammoth.convert_to_markdown(file)
        return result.value.strip()

    else:
        raise NotImplementedError('README type `{}` is not supported.'.format(ext))
