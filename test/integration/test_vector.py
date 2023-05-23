import geopandas
import pytest
import xarray

from geocube.vector import vectorize
from test.conftest import TEST_COMPARE_DATA_DIR


@pytest.mark.parametrize("mask_and_scale", [True, False])
def test_vectorize(mask_and_scale):
    xds = xarray.open_dataset(
        TEST_COMPARE_DATA_DIR / "soil_grid_flat.nc",
        decode_coords="all",
        mask_and_scale=mask_and_scale,
    )
    gdf = vectorize(xds.om_r)
    assert isinstance(gdf, geopandas.GeoDataFrame)
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
