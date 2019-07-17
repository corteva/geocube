# -- coding: utf-8 --
"""
This module contains tools for rasterizing vector data.
"""
import numpy
import rasterio.features
import rasterio.transform
import rasterio.warp
from scipy.interpolate import griddata, Rbf
from shapely.geometry import mapping

from geocube.logger import get_logger


def rasterize_image(
    geometry_array, data_values, geobox, fill=-9999.0, **ignored_kwargs
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
    fill: float, optional
        The value to fill in the grid with for nodata. Default is -9999.0.
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
        image = rasterio.features.rasterize(
            zip(geometry_array.apply(mapping).values, data_values),
            out_shape=(geobox.height, geobox.width),
            transform=geobox.affine,
            fill=fill,
            dtype=numpy.float64,
        )
        return image
    except TypeError as ter:
        if "cannot perform reduce with flexible type" in str(ter):
            logger.warning("{warning}".format(warning=ter))
            return None
        raise


def rasterize_points_griddata(
    geometry_array,
    data_values,
    grid_coords,
    fill=-9999.0,
    method="nearest",
    **ignored_kwargs
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
    fill: float, optional
        The value to fill in the grid with for nodata. Default is -9999.0.
    method: {‘linear’, ‘nearest’, ‘cubic’}, optional
        The method to use for interpolation in `scipy.interpolate.griddata`.
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
        return griddata(
            points=(geometry_array.x, geometry_array.y),
            values=data_values,
            xi=tuple(numpy.meshgrid(grid_coords["x"], grid_coords["y"])),
            method=method,
            fill_value=fill,
        )
    except ValueError as ver:
        if "could not convert string to float" in str(ver):
            return None
        raise


def rasterize_points_radial(
    geometry_array, data_values, grid_coords, method="linear", **ignored_kwargs
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
    fill: float, optional
        The value to fill in the grid with for nodata. Default is -9999.0.
    method: str, optional
        The function to use for interpolation in `scipy.interpolate.Rbf`.
        {'multiquadric', 'inverse', 'gaussian', 'linear',
        'cubic', 'quintic', 'thin_plate'}
    **ignored_kwargs:
        These are there to be flexible with additional rasterization methods and
        will be ignored.

    Returns
    -------
    :class:`numpy.ndarray`: An interpolated :class:`numpy.ndarray`.

    """
    logger = get_logger()

    try:
        interp = Rbf(geometry_array.x, geometry_array.y, data_values, function=method)
        return interp(*numpy.meshgrid(grid_coords["x"], grid_coords["y"]))
    except ValueError as ter:
        if "object arrays are not supported" in str(ter):
            logger.warning("{warning}".format(warning=ter))
            return None
        raise
