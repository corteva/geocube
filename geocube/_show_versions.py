"""
Utility methods to print system info for debugging

adapted from :func:`sklearn.utils._show_versions`
which was adapted from :func:`pandas.show_versions`
"""
# pylint: disable=import-outside-toplevel
import importlib
import platform
import sys


def _get_sys_info():
    """System information
    Return
    ------
    sys_info : dict
        system and Python version information
    """
    blob = [
        ("python", sys.version.replace("\n", " ")),
        ("executable", sys.executable),
        ("machine", platform.platform()),
    ]

    return dict(blob)


def _get_gdal_info():
    """Get the GDAL dependency information.

    Returns
    -------
    proj_info: dict
        system GDAL information
    """
    import fiona
    import rasterio

    blob = [
        ("fiona", fiona.__version__),
        ("GDAL[fiona]", fiona.__gdal_version__),
        ("rasterio", rasterio.__version__),
        ("GDAL[rasterio]", rasterio.__gdal_version__),
    ]

    return dict(blob)


def _get_deps_info():
    """Overview of the installed version of dependencies
    Returns
    -------
    deps_info: dict
        version information on relevant Python libraries
    """
    deps = [
        "appdirs",
        "click",
        "datacube",
        "geopandas",
        "rioxarray",
        "pyproj",
        "xarray",
    ]

    def get_version(module):
        try:
            return module.__version__
        except AttributeError:
            return module.version

    deps_info = {}

    for modname in deps:
        try:
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = importlib.import_module(modname)
            ver = get_version(mod)
            deps_info[modname] = ver
        except ImportError:
            deps_info[modname] = None

    return deps_info


def _print_info_dict(info_dict):
    """Print the information dictionary"""
    for key, stat in info_dict.items():
        print("{key:>14}: {stat}".format(key=key, stat=stat))


def show_versions():
    """
    .. versionadded:: 0.0.12

    Print useful debugging information

    Example
    -------
    > python -c "import geocube; geocube.show_versions()"

    """
    import geocube  # pylint: disable=cyclic-import

    print(f"geocube v{geocube.__version__}\n")
    print("GDAL deps:")
    _print_info_dict(_get_gdal_info())
    print("\nPython deps:")
    _print_info_dict(_get_deps_info())
    print("\nSystem:")
    _print_info_dict(_get_sys_info())
