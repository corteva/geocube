import geopandas
import pytest
import xarray
from numpy.testing import assert_almost_equal

from geocube.vector import vectorize
from test.conftest import TEST_COMPARE_DATA_DIR


@pytest.mark.parametrize("invert_y", [True, False])
@pytest.mark.parametrize("mask_and_scale", [True, False])
def test_vectorize(mask_and_scale, invert_y):
    xds = xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        decode_coords="all",
        mask_and_scale=mask_and_scale,
    )
    if invert_y:
        # https://github.com/corteva/geocube/issues/165
        xds.rio.write_transform(xds.rio.transform(), inplace=True)
        xds = xds.sortby("y")
    gdf = vectorize(xds.om_r)
    assert isinstance(gdf, geopandas.GeoDataFrame)
    assert_almost_equal(gdf.total_bounds, [700330, 4595210, 701750, 4597070])
    assert gdf.dtypes.astype(str).to_dict() == {
        "geometry": "geometry",
        "om_r": "float64",
    }
    assert not gdf.geometry.isnull().any()
    if mask_and_scale:
        assert not gdf.om_r.isnull().any()
    else:
        assert not (gdf.om_r == xds.om_r.rio.nodata).any()
    assert len(gdf.index) == 7


def test_vectorize__missing_nodata():
    xds = xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        decode_coords="all",
        mask_and_scale=False,
    )
    xds.om_r.attrs.pop("_FillValue")
    gdf = vectorize(xds.om_r)
    assert isinstance(gdf, geopandas.GeoDataFrame)
    assert gdf.dtypes.astype(str).to_dict() == {
        "geometry": "geometry",
        "om_r": "float64",
    }
    assert not gdf.geometry.isnull().any()
    assert not gdf.om_r.isnull().any()
    assert len(gdf.index) == 8


def test_vectorize__no_name():
    xds = xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        decode_coords="all",
        mask_and_scale=False,
    )

    test_array = xarray.DataArray(xds.om_r.data)

    with pytest.warns(UserWarning):
        gdf = vectorize(test_array)

    assert "_data" in gdf.columns
