from geocube import show_versions
from geocube._show_versions import _get_deps_info, _get_gdal_info, _get_sys_info


def test_get_gdal_info():
    gdal_info = _get_gdal_info()
    assert "rasterio" in gdal_info
    assert "GDAL[rasterio]" in gdal_info
    assert "pyogrio" in gdal_info
    assert "GDAL[pyogrio]" in gdal_info


def test_get_sys_info():
    sys_info = _get_sys_info()

    assert "python" in sys_info
    assert "executable" in sys_info
    assert "machine" in sys_info


def test_get_deps_info():
    deps_info = _get_deps_info()

    assert "rioxarray" in deps_info
    assert "geopandas" in deps_info
    assert "pyproj" in deps_info
    assert "xarray" in deps_info
    assert "odc_geo" in deps_info
    assert "click" in deps_info
    assert "appdirs" in deps_info


def test_show_versions_with_proj(capsys):
    show_versions()
    out, err = capsys.readouterr()
    assert "System" in out
    assert "python" in out
    assert "GDAL deps" in out
    assert "geocube" in out
    assert "Python deps" in out
