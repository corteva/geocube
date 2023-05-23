"""
Module for vector methods
"""
import geopandas
import numpy
import rasterio.features
import rioxarray  # noqa: F401 pylint: disable=unused-import
import shapely.geometry
import xarray


def vectorize(data_array: xarray.DataArray) -> geopandas.GeoDataFrame:
    """
    .. versionadded:: 0.4.0

    Powered by: :func:`rasterio.features.shapes`

    Convert 2D :class:`xarray.DataArray` into
    a :class:`geopandas.GeoDataFrame`.

    The ``nodata``,  ``CRS``, and ``transform`` of the :class:`xarray.DataArray`
    are determined using ``rioxarray``.

    Helpful references:

    - https://corteva.github.io/rioxarray/stable/getting_started/crs_management.html
    - https://corteva.github.io/rioxarray/stable/getting_started/nodata_management.html


    Parameters
    ----------
    data_array: xarray.DataArray
        Input 2D DataArray raster.

    Returns
    -------
    geopandas.GeoDataFrame
    """
    # nodata mask
    mask = None
    if data_array.rio.nodata is not None:
        if numpy.isnan(data_array.rio.nodata):
            mask = ~data_array.isnull()
        else:
            mask = data_array != data_array.rio.nodata

    # vectorize generator
    vectorized_data = (
        (value, shapely.geometry.shape(polygon))
        for polygon, value in rasterio.features.shapes(
            data_array,
            transform=data_array.rio.transform(),
            mask=mask,
        )
    )
    return geopandas.GeoDataFrame(
        vectorized_data,
        columns=[data_array.name, "geometry"],
        crs=data_array.rio.crs,
    )
