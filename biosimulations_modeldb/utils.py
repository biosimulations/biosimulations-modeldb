from biosimulators_utils.biosimulations.utils import get_file_extension_combine_uri_map as base_get_file_extension_combine_uri_map
from biosimulators_utils.combine.data_model import CombineArchiveContentFormat
import glob
import warnings

__all__ = ['get_file_extension_combine_uri_map', 'case_insensitive_glob']


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

        map[ext] = list(uris)[0]

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
