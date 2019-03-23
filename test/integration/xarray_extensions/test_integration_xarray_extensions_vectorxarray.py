import os

import geopandas as gpd
import pytest
import xarray
from dateutil.parser import parse
from numpy.testing import assert_array_equal

from geocube.xarray_extensions import vectorxarray
from test.conftest import TEST_INPUT_DATA_DIR


def assert_test_dataframes_equal(gdf, gdf2):
    assert gdf.crs == gdf2.crs
    assert sorted(gdf.columns) == sorted(gdf2.columns)
    for column in gdf.columns:
        assert_array_equal(gdf[column], gdf2[column])


def test_from_geodataframe():
    gdf = gpd.read_file(os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"))
    vxd = vectorxarray.from_geodataframe(gdf)
    assert all(gdf.geometry == vxd.geometry.values)
    assert sorted(gdf.columns.tolist() + ["crs"]) == sorted(vxd.variables)
    assert gdf.crs == vxd.crs.attrs
    assert "geometry" in vxd.coords
    assert "crs" in vxd.coords


def test_to_geodataframe():
    gdf = gpd.read_file(os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"))
    gdf2 = vectorxarray.from_geodataframe(gdf).vector.to_geodataframe()
    assert_test_dataframes_equal(gdf, gdf2)


def test_to_netcdf(tmpdir):
    gdf = gpd.read_file(os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"))
    vxd = vectorxarray.from_geodataframe(gdf)
    output_file = tmpdir.join("test_vector.nc")
    vxd.vector.to_netcdf(output_file)
    vxd2 = vectorxarray.open_dataset(str(output_file))
    assert_test_dataframes_equal(gdf, vxd2.vector.to_geodataframe())


def test_multidimensional_error():
    gdf = gpd.read_file(os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"))
    vxd = vectorxarray.from_geodataframe(gdf)
    vxd2 = vxd.copy()
    vxd.coords["time"] = parse("20170516T000000")
    vxd2.coords["time"] = parse("20170517T000000")
    merged_vxd = xarray.concat([vxd, vxd2], dim="time")
    with pytest.raises(ValueError):
        merged_vxd.vector.plot(column="sandtotal_r")
