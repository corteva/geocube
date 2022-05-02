import numpy
import rioxarray  # noqa: F401 pylint: disable=unused-import
import xarray

from geocube.geo_utils.geobox import geobox_from_rio


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
