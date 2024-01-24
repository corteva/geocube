import importlib.metadata
import json
from functools import partial

import geopandas
import numpy
import pandas
import pytest
import xarray
from numpy.testing import assert_almost_equal
from packaging import version
from rasterio.enums import MergeAlg
from shapely.geometry import Polygon, mapping
from shapely.wkt import loads

from geocube.api.core import make_geocube
from geocube.exceptions import VectorDataError
from geocube.rasterize import (
    _INT8_SUPPORTED,
    rasterize_image,
    rasterize_points_griddata,
    rasterize_points_radial,
)
from test.conftest import TEST_COMPARE_DATA_DIR, TEST_INPUT_DATA_DIR

SCIPY_LT_14 = version.parse(importlib.metadata.version("scipy")) < version.parse(
    "1.4.0"
)

TEST_GARS_PROJ = "epsg:32615"
TEST_GARS_POLY = loads(
    "POLYGON (("
    "-90.58343333333333 41.48343333333334, "
    "-90.59989999999999 41.48343333333334, "
    "-90.59989999999999 41.4999, "
    "-90.58343333333333 41.4999, "
    "-90.58343333333333 41.48343333333334"
    "))"
)


@pytest.mark.parametrize(
    "input_geodata",
    [
        str(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
        pandas.DataFrame(
            geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")
        ),
    ],
)
def test_make_geocube(input_geodata, tmpdir):
    soil_attribute_list = [
        "om_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
        "cec7_r",
        "ph1to1h2o_r",
        "dbthirdbar_r",
        "awc_r",
    ]

    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=[-10, 10],
        fill=-9999.0,
    )
    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)


def test_make_geocube__categorical(tmpdir):
    input_geodata = geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")
    input_geodata["soil_type"] = [
        "sand",
        "silt",
        "clay",
        "frank",
        "silt",
        "clay",
        "sand",
    ]
    category_type = pandas.api.types.CategoricalDtype(
        categories=["clay", "sand", "silt", "nodata"]
    )
    input_geodata["soil_type"] = input_geodata["soil_type"].astype(category_type)
    out_grid = make_geocube(
        vector_data=input_geodata,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        fill=-9999.0,
    )
    assert out_grid.soil_type.dtype.name == "int8" if _INT8_SUPPORTED else "int16"
    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_categorical.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_categorical.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)


def test_make_geocube__categorical__enums(tmpdir):
    input_geodata = geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")
    input_geodata["soil_type"] = [
        "sand",
        "silt",
        "clay",
        "frank",
        "silt",
        "clay",
        "sand",
    ]
    out_grid = make_geocube(
        vector_data=input_geodata,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        categorical_enums={"soil_type": ("sand", "silt", "clay")},
        fill=-9999.0,
    )
    assert out_grid.soil_type.dtype.name == "int8" if _INT8_SUPPORTED else "int16"

    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_categorical.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_categorical.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)


def test_make_geocube__categorical__ignore_missing_measurement(tmpdir):
    input_geodata = geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")
    input_geodata["soil_type"] = [
        "sand",
        "silt",
        "clay",
        "frank",
        "silt",
        "clay",
        "sand",
    ]
    input_geodata["ignore_soil_type"] = input_geodata["soil_type"].copy()
    category_type = pandas.api.types.CategoricalDtype(
        categories=["sand", "silt", "clay", "nodata"]
    )
    input_geodata["ignore_soil_type"] = input_geodata["ignore_soil_type"].astype(
        category_type
    )
    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=["soil_type"],
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        categorical_enums={"soil_type": ("sand", "silt", "clay")},
        fill=-9999.0,
    )
    assert out_grid.soil_type.dtype.name == "int8" if _INT8_SUPPORTED else "int16"
    assert list(out_grid.data_vars) == ["soil_type"]
    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_categorical.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_categorical.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid["soil_type"], xdc["soil_type"])


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
    ],
)
def test_make_geocube__interpolate_na(input_geodata, tmpdir):
    soil_attribute_list = [
        "om_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
        "cec7_r",
        "ph1to1h2o_r",
        "dbthirdbar_r",
        "awc_r",
    ]

    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        interpolate_na_method="nearest",
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_interpolate_na.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_interpolate_na.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
    ],
)
def test_make_geocube__like(input_geodata, tmpdir):
    soil_attribute_list = [
        "om_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
        "cec7_r",
        "ph1to1h2o_r",
        "dbthirdbar_r",
        "awc_r",
    ]

    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        out_grid = make_geocube(
            vector_data=input_geodata,
            measurements=soil_attribute_list,
            like=xdc,
            fill=-9999.0,
        )

        # test writing to netCDF
        out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat.nc")
        xarray.testing.assert_allclose(out_grid, xdc)


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
    ],
)
def test_make_geocube__only_resolution(input_geodata, tmpdir):
    soil_attribute_list = [
        "om_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
        "cec7_r",
        "ph1to1h2o_r",
        "dbthirdbar_r",
        "awc_r",
    ]

    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        resolution=(-0.001, 0.001),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_original_crs.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_original_crs.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "naive_time_vector_data.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "naive_time_vector_data.geojson"),
        TEST_INPUT_DATA_DIR / "time_vector_data.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "time_vector_data.geojson"),
    ],
)
def test_make_geocube__convert_time(input_geodata, tmpdir):
    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=["test_attr", "test_time_attr", "test_str_attr"],
        datetime_measurements=["test_time_attr"],
        resolution=(-0.00001, 0.00001),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("geocube_time") / "time_vector_data.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "time_vector_data.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    assert out_grid.test_time_attr.attrs["units"] == "seconds from 1970-01-01T00:00:00"
    assert out_grid.test_time_attr.attrs["_FillValue"] == 0


@pytest.mark.parametrize(
    "load_extra_kwargs",
    [
        {"output_crs": "epsg:4326"},
        {"resolution": (-10, 10)},
        {"align": (0, 0)},
        {"output_crs": "epsg:4326", "resolution": (-10, 10), "align": (0, 0)},
    ],
)
def test_make_geocube__like_error_invalid_args(load_extra_kwargs):
    soil_attribute_list = [
        "om_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
        "cec7_r",
        "ph1to1h2o_r",
        "dbthirdbar_r",
        "awc_r",
    ]

    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        with pytest.raises(AssertionError):
            make_geocube(
                vector_data=TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
                measurements=soil_attribute_list,
                like=xdc,
                fill=-9999.0,
                **load_extra_kwargs,
            )


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson"),
    ],
)
def test_make_geocube__no_measurements(input_geodata, tmpdir):
    out_grid = make_geocube(
        vector_data=input_geodata,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


def test_make_geocube__no_geom(tmpdir):
    out_grid = make_geocube(
        vector_data=TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
        measurements=["sandtotal_r"],
        resolution=(-0.001, 0.001),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_no_geom.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat_no_geom.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [
        geopandas.GeoDataFrame(columns=["test_col", "geometry"]),
        geopandas.GeoDataFrame(),
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson").drop(
            columns="geometry"
        ),
    ],
)
def test_make_geocube__invalid_gdf(input_geodata):
    with pytest.raises(VectorDataError):
        make_geocube(vector_data=input_geodata, resolution=(-0.001, 0.001))


def test_make_geocube__no_resolution_error():
    with pytest.raises(RuntimeError):
        make_geocube(
            vector_data=TEST_INPUT_DATA_DIR / "soil_data_flat.geojson",
            measurements=["sandtotal_r"],
            output_crs=TEST_GARS_PROJ,
            geom=json.dumps(mapping(TEST_GARS_POLY)),
            fill=-9999.0,
        )


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_group.geojson"),
    ],
)
def test_make_geocube__group_by(input_geodata, tmpdir):
    soil_attribute_list = [
        "cokey",
        "mukey",
        "drclassdcd",
        "hzdept_r",
        "hzdepb_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
    ]
    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        group_by="hzdept_r",
        resolution=(-10, 10),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_group.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_group.geojson")],
)
def test_make_geocube__group_by__categorical(input_geodata, tmpdir):
    input_geodata["soil_type"] = [
        "sand",
        "bob",
        "clay",
        "sand",
        "silt",
        "clay",
        "sand",
    ] * 11
    soil_attribute_list = ["sandtotal_r", "silttotal_r", "soil_type", "claytotal_r"]
    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        group_by="hzdept_r",
        resolution=(-10, 10),
        categorical_enums={"soil_type": ("sand", "silt", "clay")},
        fill=-9999.0,
    )

    assert out_grid.soil_type.dtype.name == "int8" if _INT8_SUPPORTED else "int16"
    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_group_categorical.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group_categorical.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_group.geojson"),
    ],
)
def test_make_geocube__group_by_like(input_geodata, tmpdir):
    soil_attribute_list = [
        "cokey",
        "mukey",
        "drclassdcd",
        "hzdept_r",
        "hzdepb_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
    ]

    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        out_grid = make_geocube(
            vector_data=input_geodata,
            measurements=soil_attribute_list,
            group_by="hzdept_r",
            like=xdc,
            fill=-9999.0,
        )

        # test writing to netCDF
        out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_group.nc")

        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_group.geojson"),
    ],
)
def test_make_geocube__group_by_only_resolution(input_geodata, tmpdir):
    soil_attribute_list = ["sandtotal_r", "silttotal_r", "claytotal_r"]

    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=soil_attribute_list,
        group_by="hzdept_r",
        resolution=(-0.001, 0.001),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(
        tmpdir.mkdir("make_geocube_soil") / "soil_grid_grouped_original_crs.nc"
    )

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_grouped_original_crs.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "time_vector_data.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "time_vector_data.geojson"),
    ],
)
def test_make_geocube__group_by_time(input_geodata, tmpdir):
    out_grid = make_geocube(
        vector_data=input_geodata,
        datetime_measurements=["test_time_attr"],
        resolution=(-0.00001, 0.00001),
        group_by="test_time_attr",
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_time") / "vector_time_data_group.nc")
    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "vector_time_data_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "time_vector_data.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "time_vector_data.geojson"),
    ],
)
def test_make_geocube__group_by_convert_with_time(input_geodata, tmpdir):
    out_grid = make_geocube(
        vector_data=input_geodata,
        datetime_measurements=["test_time_attr"],
        resolution=(-0.00001, 0.00001),
        group_by="test_attr",
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_time") / "vector_data_group.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "vector_data_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    assert out_grid.test_time_attr.attrs["units"] == "seconds from 1970-01-01T00:00:00"
    assert out_grid.test_time_attr.attrs["_FillValue"] == 0

    tmpdir.remove()


@pytest.mark.parametrize(
    "load_extra_kwargs",
    [
        {"output_crs": "epsg:4326"},
        {"resolution": (-10, 10)},
        {"align": (0, 0)},
        {"output_crs": "epsg:4326", "resolution": (-10, 10), "align": (0, 0)},
    ],
)
def test_make_geocube__group_by_like_error_invalid_args(load_extra_kwargs):
    soil_attribute_list = [
        "cokey",
        "mukey",
        "drclassdcd",
        "hzdept_r",
        "hzdepb_r",
        "sandtotal_r",
        "silttotal_r",
        "claytotal_r",
    ]

    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        with pytest.raises(AssertionError):
            make_geocube(
                vector_data=TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
                measurements=soil_attribute_list,
                like=xdc,
                group_by="hzdept_r",
                fill=-9999.0,
                **load_extra_kwargs,
            )


@pytest.mark.parametrize(
    "input_geodata",
    [
        TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
        geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_group.geojson"),
    ],
)
def test_make_geocube__group_by_no_measurements(input_geodata, tmpdir):
    out_grid = make_geocube(
        vector_data=input_geodata,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        group_by="hzdept_r",
        resolution=(-10, 10),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_group.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


def test_make_geocube__group_by__no_geom(tmpdir):
    out_grid = make_geocube(
        vector_data=TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
        measurements=["sandtotal_r"],
        group_by="hzdept_r",
        resolution=(-0.001, 0.001),
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_group_no_geom.nc")

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_group_no_geom.nc",
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc)

    tmpdir.remove()


def test_make_geocube__group_by__no_resolution_error():
    with pytest.raises(RuntimeError):
        make_geocube(
            vector_data=TEST_INPUT_DATA_DIR / "soil_data_group.geojson",
            measurements=["sandtotal_r"],
            output_crs=TEST_GARS_PROJ,
            geom=json.dumps(mapping(TEST_GARS_POLY)),
            group_by="hzdept_r",
            fill=-9999.0,
        )


def test_make_geocube__new_bounds_crs():
    utm_cube = make_geocube(
        vector_data=TEST_INPUT_DATA_DIR / "wgs84_geom.geojson",
        output_crs="epsg:32614",
        resolution=(-1, 1),
        fill=-9999.0,
    )
    assert_almost_equal(
        utm_cube.id.rio.bounds(), (1665478.0, 7018306.0, 1665945.0, 7018509.0)
    )


@pytest.mark.parametrize(
    "function,compare_name",
    [
        (rasterize_points_griddata, "rasterize_griddata_nearest.nc"),
        (
            partial(rasterize_points_griddata, rescale=True),
            "rasterize_griddata_rescale.nc",
        ),
        (
            partial(rasterize_points_griddata, method="cubic"),
            "rasterize_griddata_cubic.nc",
        ),
        (rasterize_points_radial, "rasterize_radial_linear.nc"),
        (partial(rasterize_image, merge_alg=MergeAlg.add), "rasterize_image_sum.nc"),
        (partial(rasterize_image, all_touched=True), "rasterize_unchanged.nc"),
    ],
)
@pytest.mark.xfail(
    SCIPY_LT_14,
    reason="griddata behaves differently across versions",
)
def test_make_geocube__custom_rasterize_function(function, compare_name, tmpdir):
    input_geodata = TEST_INPUT_DATA_DIR / "time_vector_data.geojson"
    out_grid = make_geocube(
        vector_data=input_geodata,
        measurements=["test_attr", "test_time_attr", "test_str_attr"],
        resolution=(-0.00001, 0.00001),
        rasterize_function=function,
        fill=-9999.0,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("geocube_custom") / compare_name)

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / compare_name,
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc, rtol=0.1, atol=0.1)


@pytest.mark.parametrize(
    "function,compare_name",
    [
        (
            partial(rasterize_points_griddata, filter_nan=True),
            "rasterize_griddata_nearest_nodata.nc",
        ),
        (
            partial(rasterize_points_griddata, method="cubic", filter_nan=True),
            "rasterize_griddata_cubic_nodata.nc",
        ),
        (
            partial(rasterize_points_radial, filter_nan=True),
            "rasterize_radial_linear_nodata.nc",
        ),
        (
            partial(rasterize_image, merge_alg=MergeAlg.add, filter_nan=True),
            "rasterize_image_sum_nodata.nc",
        ),
    ],
)
@pytest.mark.xfail(
    SCIPY_LT_14,
    reason="griddata behaves differently across versions",
)
def test_make_geocube__custom_rasterize_function__filter_null(
    function, compare_name, tmpdir
):
    input_geodata = TEST_INPUT_DATA_DIR / "point_with_null.geojson"
    out_grid = make_geocube(
        vector_data=input_geodata,
        resolution=(-0.00001, 0.00001),
        rasterize_function=function,
    )

    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("geocube_custom") / compare_name)

    # test output data
    with xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / compare_name,
        mask_and_scale=False,
        decode_coords="all",
    ) as xdc:
        xarray.testing.assert_allclose(out_grid, xdc, rtol=0.1, atol=0.1)


@pytest.mark.parametrize(
    "dtype,fill,expected_type",
    [
        ("uint16", 0, "uint16"),
        ("uint16", float("NaN"), "float32"),
        ("int32", 0, "int32"),
        ("int32", float("NaN"), "float64"),
        ("int64", 0, "int64"),
        ("int64", float("NaN"), "float64"),
    ],
)
def test_make_geocube__minimize_dtype(dtype, fill, expected_type, tmpdir):
    gdf = geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")
    gdf["mask"] = 1
    gdf["mask"] = gdf["mask"].astype(dtype)
    out_grid = make_geocube(
        vector_data=gdf,
        measurements=["mask"],
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=(-10, 10),
        fill=fill,
    )
    assert out_grid.mask.dtype.name == expected_type
    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat_mask.nc")


def test_rasterize__like_1d():
    like = xarray.open_dataset(
        TEST_INPUT_DATA_DIR / "one_dimensional.nc", decode_coords="all"
    )
    geom = Polygon(
        [
            (-93.90054499995499, 41.687572053080224),
            (-93.900635000045, 41.687572053080224),
            (-93.900635000045, 41.68770794691978),
            (-93.90054499995499, 41.68770794691978),
        ]
    )

    geom_array = make_geocube(
        geopandas.GeoDataFrame({"in_geom": [1]}, geometry=[geom], crs="epsg:4326"),
        like=like,
    )
    assert geom_array.rio.transform() == like.rio.transform()
    assert geom_array.in_geom.shape == (2, 1)


@pytest.mark.parametrize(
    "dtype, expected_dtype",
    [
        ("Int32", "int32"),
        ("Int64", "int64"),
    ],
)
def test_make_geocube__pandas_integer_array(dtype, expected_dtype, tmpdir):
    soil_data = geopandas.read_file(TEST_INPUT_DATA_DIR / "soil_data_flat.geojson")[
        ["geometry", "sandtotal_r", "om_r"]
    ]
    soil_data["sandtotal_r"] = numpy.round(soil_data["sandtotal_r"] * 100).astype(dtype)
    soil_data["sandtotal_r"].values[0] = pandas.NA

    out_grid = make_geocube(
        vector_data=soil_data,
        output_crs=TEST_GARS_PROJ,
        geom=json.dumps(mapping(TEST_GARS_POLY)),
        resolution=[-10, 10],
        fill=-1,
    )
    # test writing to netCDF
    out_grid.to_netcdf(tmpdir.mkdir("make_geocube_soil") / "soil_grid_flat.nc")
    assert out_grid.sandtotal_r.dtype.name == expected_dtype
