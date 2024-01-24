import geopandas
import numpy
import rioxarray  # noqa: F401 pylint: disable=unused-import
import xarray

from geocube.geo_utils.geobox import geobox_from_rio, load_vector_data
from test.conftest import TEST_INPUT_DATA_DIR


def test_geobox_from_rio__no_epsg():
    # https://github.com/opendatacube/odc-geo/pull/41
    crs_wkt = (
        'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",'
        'DATUM["Not specified (based on custom spheroid)",'
        'SPHEROID["Custom spheroid",6371007.181,0]],'
        'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
        'PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],'
        'PARAMETER["false_easting",0],PARAMETER["false_northing",0],'
        'UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
    )
    test_da = xarray.DataArray(
        numpy.zeros((5, 5)),
        dims=("y", "x"),
        coords={"y": numpy.arange(1, 6), "x": numpy.arange(2, 7)},
    )
    test_da.rio.write_crs(crs_wkt, inplace=True)
    geobox = geobox_from_rio(test_da)
    assert geobox.crs == crs_wkt


def test_load_vector_data__measurements(tmp_path):
    file_to_read = tmp_path / "test.gpkg"
    geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson").to_file(
        file_to_read, driver="GPKG"
    )
    data = load_vector_data(
        file_to_read,
        measurements=[
            "om_r",
            "sandtotal_r",
        ],
    )
    assert data.columns.tolist() == ["om_r", "sandtotal_r", "geometry"]


def test_load_vector_data__measurements__no_driver_support():
    data = load_vector_data(
        TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        measurements=[
            "om_r",
            "sandtotal_r",
        ],
    )
    assert data.columns.tolist() == ["om_r", "sandtotal_r", "geometry"]
