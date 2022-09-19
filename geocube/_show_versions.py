"""
Utility methods to print system info for debugging

adapted from :func:`sklearn.utils._show_versions`
which was adapted from :func:`pandas.show_versions`
"""
# pylint: disable=import-outside-toplevel
import importlib.metadata
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
        ("fiona", importlib.metadata.version("fiona")),
        ("GDAL[fiona]", fiona.__gdal_version__),
        ("rasterio", importlib.metadata.version("rasterio")),
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
        "geopandas",
        "odc_geo",
        "rioxarray",
        "pyproj",
        "xarray",
    ]

    def get_version(module):
        try:
            return importlib.metadata.version(module)
        except importlib.metadata.PackageNotFoundError:
            return None

    return {dep: get_version(dep) for dep in deps}


def _print_info_dict(info_dict):
    """Print the information dictionary"""
    for key, stat in info_dict.items():
        print(f"{key:>14}: {stat}")


def show_versions():
    """
    .. versionadded:: 0.0.12

    Print useful debugging information

    Example
    -------
    > python -c "import geocube; geocube.show_versions()"

    """
    print(f"geocube v{importlib.metadata.version('geocube')}\n")
    print("GDAL deps:")
    _print_info_dict(_get_gdal_info())
    print("\nPython deps:")
    _print_info_dict(_get_deps_info())
    print("\nSystem:")
    _print_info_dict(_get_sys_info())
