"""
This module contains tools for rasterizing vector data.
"""
from typing import Optional

import geopandas
import numpy
import odc.geo.geobox
import pandas
import rasterio.features
from numpy.typing import NDArray
from rasterio.enums import MergeAlg
from scipy.interpolate import Rbf, griddata


def _is_numeric(data_values: NDArray) -> bool:
    """
    Check if array data type is numeric.
    """
    return numpy.issubdtype(data_values.dtype.type, numpy.number)


def _remove_missing_data(
    data_values: NDArray,
    geometry_array: geopandas.GeoSeries,
) -> tuple[NDArray, geopandas.GeoSeries]:
    """
    Missing data causes issues with interpolation of point data
    https://github.com/corteva/geocube/issues/9

    This filters the data so those issues don't cause problems.
    """
    not_missing_data = ~pandas.isnull(data_values)
    geometry_array = geometry_array[not_missing_data]
    data_values = data_values[not_missing_data]
    return data_values, geometry_array


def _minimize_dtype(dtype: numpy.dtype, fill: float) -> numpy.dtype:
    """
    If int64, convert to float64:
    https://github.com/OSGeo/gdal/issues/3325

    Attempt to convert to float32 if fill is NaN and dtype is integer.
    """
    if numpy.issubdtype(dtype, numpy.integer):
        if dtype.name == "int8":
            # GDAL/rasterio doesn't support int8
            dtype = numpy.dtype("int16")
        if dtype.name == "int64":
            # GDAL/rasterio doesn't support int64
            dtype = numpy.dtype("float64")
        if numpy.isnan(fill):
            dtype = (
                numpy.dtype("float64") if dtype.itemsize > 2 else numpy.dtype("float32")  # type: ignore
            )
    elif not numpy.issubdtype(dtype, numpy.floating):
        # default to float64 for non-integer/float types
        dtype = numpy.dtype("float64")
    return dtype


def rasterize_image(
    geometry_array: geopandas.GeoSeries,
    data_values: NDArray,
    geobox: odc.geo.geobox.GeoBox,
    fill: float,
    merge_alg: MergeAlg = MergeAlg.replace,
    filter_nan: bool = False,
    all_touched: bool = False,
    **ignored_kwargs,
) -> Optional[NDArray]:
    """
    Rasterize a list of shapes+values for a given GeoBox.

    Parameters
    -----------
    geometry_array: geopandas.GeoSeries
        A geometry array of points.
    data_values: list
        Data values associated with the list of geojson shapes
    geobox: :obj:`odc.geo.geobox.GeoBox`
        Transform of the resulting image.
    fill: float
        The value to fill in the grid with for nodata.
    merge_alg: `rasterio.enums.MergeAlg`, optional
        The algorithm for merging values into one cell. Default is `MergeAlg.replace`.
    filter_nan: bool, optional
        If True, will remove nodata values from the data before rasterization.
        Default is False.
    all_touched: bool, optional
        Passed to rasterio.features.rasterize. If True, all pixels touched by
        geometries will be burned in. If false, only pixels whose center is
        within the polygon or that are selected by Bresenham’s line algorithm
        will be burned in.
    **ignored_kwargs:
        These are there to be flexible with additional rasterization methods and
        will be ignored.

    Returns
    -------
    :obj:`numpy.ndarray` or None
        The vector data in the rasterized format.

    """
    if not _is_numeric(data_values):
        # only numbers can be rasterized
        return None

    if filter_nan:
        data_values, geometry_array = _remove_missing_data(data_values, geometry_array)

    image = rasterio.features.rasterize(
        zip(geometry_array.values, data_values),
        out_shape=(geobox.height, geobox.width),
        transform=geobox.affine,
        fill=fill,
        all_touched=all_touched,
        merge_alg=merge_alg,
        dtype=_minimize_dtype(data_values.dtype, fill),
    )
    return image


def rasterize_points_griddata(
    geometry_array: geopandas.GeoSeries,
    data_values: NDArray,
    grid_coords: dict[str, NDArray],
    fill: float,
    method: str = "nearest",
    rescale: bool = False,
    filter_nan: bool = False,
    **ignored_kwargs,
) -> Optional[NDArray]:
    """
    This method uses scipy.interpolate.griddata to interpolate point data
    to a grid.

    Parameters
    ----------
    geometry_array: geopandas.GeoSeries
        A geometry array of points.
    data_values: list
        Data values associated with the list of geojson shapes
    grid_coords: dict
        Output from `rioxarray.rioxarray.affine_to_coords`
    fill: float
        The value to fill in the grid with for nodata.
    method: {'linear', 'nearest', 'cubic'}, optional
        The method to use for interpolation in `scipy.interpolate.griddata`.
    rescale: bool, optional
        Rescale points to unit cube before performing interpolation. Default is false.
    filter_nan: bool, optional
        If True, will remove nodata values from the data before rasterization.
        Default is False.
    **ignored_kwargs:
        These are there to be flexible with additional rasterization methods and
        will be ignored.

    Returns
    -------
    :class:`numpy.ndarray`: An interpolated :class:`numpy.ndarray`.

    """
    if not _is_numeric(data_values):
        # only numbers can be rasterized
        return None

    if filter_nan:
        data_values, geometry_array = _remove_missing_data(data_values, geometry_array)

    return griddata(
        points=(geometry_array.x, geometry_array.y),
        values=data_values,
        xi=tuple(numpy.meshgrid(grid_coords["x"], grid_coords["y"])),
        method=method,
        fill_value=fill,
        rescale=rescale,
    )


def rasterize_points_radial(
    geometry_array: geopandas.GeoSeries,
    data_values: NDArray,
    grid_coords: dict[str, NDArray],
    method: str = "linear",
    filter_nan=False,
    **ignored_kwargs,
) -> Optional[NDArray]:
    """
    This method uses scipy.interpolate.Rbf to interpolate point data
    to a grid.

    Parameters
    ----------
    geometry_array: geopandas.GeoSeries
        A geometry array of points.
    data_values: list
        Data values associated with the list of geojson shapes
    grid_coords: dict
        Output from `rioxarray.rioxarray.affine_to_coords`
    method: str, optional
        The function to use for interpolation in `scipy.interpolate.Rbf`.
        {'multiquadric', 'inverse', 'gaussian', 'linear',
        'cubic', 'quintic', 'thin_plate'}
    filter_nan: bool, optional
        If True, will remove nodata values from the data before rasterization.
        Default is False.
    **ignored_kwargs:
        These are there to be flexible with additional rasterization methods and
        will be ignored.

    Returns
    -------
    :class:`numpy.ndarray`: An interpolated :class:`numpy.ndarray`.

    """
    if not _is_numeric(data_values):
        # only numbers can be rasterized
        return None

    if filter_nan:
        data_values, geometry_array = _remove_missing_data(data_values, geometry_array)

    interp = Rbf(geometry_array.x, geometry_array.y, data_values, function=method)
    return interp(*numpy.meshgrid(grid_coords["x"], grid_coords["y"]))
