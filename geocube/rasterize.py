# -- coding: utf-8 --
"""
This module contains tools for rasterizing vector data.
"""
import numpy
import rasterio.features
import rasterio.transform
import rasterio.warp

from geocube.logger import get_logger


def rasterize_image(geojson_shapes, data_values, geobox, fill=-9999.0):
    """
    Rasterize a list of shapes+values for a given GeoBox.

    Parameters
    -----------
    geojson_shapes: list
        List of geojson shapes to rasterize.
    data_values: list
        Data values associated with the list of geojson shapes
    geobox: :obj:`datacube.utils.geometry.GeoBox`
        Transform of the resulting image.
    fill: float, optional
        The value to fill in the grid with for nodata. Default is -9999.0.

    Returns
    -------
    :obj:`numpy.ndarray` or None
        The vector data in the rasterized format.

    """
    logger = get_logger()

    try:
        image = rasterio.features.rasterize(
            zip(geojson_shapes, data_values),
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
