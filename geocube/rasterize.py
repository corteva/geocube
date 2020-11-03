# -- coding: utf-8 --
"""
This module contains tools for rasterizing vector data.
"""
import numpy
import pandas
import rasterio.features
from rasterio.enums import MergeAlg
from scipy.interpolate import Rbf, griddata
from shapely.geometry import mapping

from geocube.logger import get_logger


def _remove_missing_data(data_values, geometry_array):
    """
    Missing data causes issues with interpolation of point data
    https://github.com/corteva/geocube/issues/9

    This filters the data so those issues don't cause problems.
    """
    not_missing_data = ~pandas.isnull(data_values)
    geometry_array = geometry_array[not_missing_data]
    data_values = data_values[not_missing_data]
    return data_values, geometry_array


def rasterize_image(
    geometry_array,
    data_values,
    geobox,
    fill,
    merge_alg=MergeAlg.replace,
    filter_nan=False,
    all_touched=False,
    **ignored_kwargs,
):
    """
    Rasterize a list of shapes+values for a given GeoBox.

    Parameters
    -----------
    geometry_array: geopandas.GeometryArray
        A geometry array of points.
    data_values: list
        Data values associated with the list of geojson shapes
    geobox: :obj:`datacube.utils.geometry.GeoBox`
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
    logger = get_logger()

    try:
        if filter_nan:
            data_values, geometry_array = _remove_missing_data(
                data_values, geometry_array
            )
        image = rasterio.features.rasterize(
            zip(geometry_array.apply(mapping).values, data_values),
            out_shape=(geobox.height, geobox.width),
            transform=geobox.affine,
            fill=fill,
            all_touched=all_touched,
            merge_alg=merge_alg,
            dtype=numpy.float64,
        )
        return image
    except TypeError as ter:
        if "cannot perform reduce with flexible type" in str(ter):
            logger.warning(f"{ter}")
            return None
        raise


def rasterize_points_griddata(
    geometry_array,
    data_values,
    grid_coords,
    fill,
    method="nearest",
    rescale=False,
    filter_nan=False,
    **ignored_kwargs,
):
    """
    This method uses scipy.interpolate.griddata to interpolate point data
    to a grid.

    Parameters
    ----------
    geometry_array: geopandas.GeometryArray
        A geometry array of points.
    data_values: list
        Data values associated with the list of geojson shapes
    grid_coords: dict
        Output from `rioxarray.rioxarray.affine_to_coords`
    fill: float
        The value to fill in the grid with for nodata.
    method: {‘linear’, ‘nearest’, ‘cubic’}, optional
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
    if data_values.dtype == object:
        return None
    try:
        if filter_nan:
            data_values, geometry_array = _remove_missing_data(
                data_values, geometry_array
            )
        return griddata(
            points=(geometry_array.x, geometry_array.y),
            values=data_values,
            xi=tuple(numpy.meshgrid(grid_coords["x"], grid_coords["y"])),
            method=method,
            fill_value=fill,
            rescale=rescale,
        )
    except ValueError as ver:
        if "could not convert string to float" in str(ver):
            return None
        raise


def rasterize_points_radial(
    geometry_array,
    data_values,
    grid_coords,
    method="linear",
    filter_nan=False,
    **ignored_kwargs,
):
    """
    This method uses scipy.interpolate.Rbf to interpolate point data
    to a grid.

    Parameters
    ----------
    geometry_array: geopandas.GeometryArray
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
    logger = get_logger()

    try:
        if filter_nan:
            data_values, geometry_array = _remove_missing_data(
                data_values, geometry_array
            )
        interp = Rbf(geometry_array.x, geometry_array.y, data_values, function=method)
        return interp(*numpy.meshgrid(grid_coords["x"], grid_coords["y"]))
    except ValueError as ter:
        if "object arrays are not supported" in str(ter):
            logger.warning(f"{ter}")
            return None
        raise
