# -- coding: utf-8 --
"""
GeoCube client core functionality
"""
import numpy

from geocube.geo_utils.geobox import GeoBoxMaker
from geocube.vector_to_cube import VectorToCube


def make_geocube(
    vector_data,
    measurements=None,
    datetime_measurements=None,
    output_crs=None,
    resolution=None,
    align=None,
    geom=None,
    like=None,
    fill=numpy.nan,
    group_by=None,
    interpolate_na_method=None,
    categorical_enums=None,
    rasterize_function=None,
):
    """
    Rasterize vector data into an ``xarray`` object.  Each attribute will be a data
    variable in the :class:`xarray.Dataset`.

    Parameters
    ----------
    vector_data: str or :obj:`geopandas.GeoDataFrame`
        A file path to an OGR supported source or GeoDataFrame containing
        the vector data.
    measurements: list(str), optional
        Attributes name or list of names to be included. If a list is specified,
        the attributes will be returned in the order requested.
        By default all available attributes are included.
    datetime_measurements: list(str), optional
        Attributes that are temporal in nature and should be converted to the datetime
        format. These are only included if listed in 'measurements'.
    output_crs: str, optional
        The CRS of the returned data.  If no CRS is supplied, the CRS of the
        stored data is used.
    resolution: (float,float), optional
        A tuple of the spatial resolution of the returned data.
        This includes the direction (as indicated by a positive or negative number).
        Typically when using most CRSs, the first number would be negative.
    align: (float,float), optional
        Load data such that point 'align' lies on the pixel boundary.
        Units are in the co-ordinate space of the output CRS.
        Default is (0,0)
    geom: str, optional
        A GeoJSON string for the bounding box of the data used to construct the
        grid.
    like: :obj:`xarray.Dataset`, optional
        Uses the output of a previous ``load()`` to form the basis of a request
        for another product.
        E.g.::

            gcds = make_geocube(vector_data='my_vector.geopackage', like=other_gcds)

    fill: float, optional
        The value to fill in the grid with for nodata. Default is NaN.
    group_by: str, optional
        When specified, perform basic combining/reducing of the data on this column.
    interpolate_na_method:  {‘linear’, ‘nearest’, ‘cubic’}, optional
        This is the method for interpolation to use to fill in the nodata with
        :meth:`scipy.interpolate.griddata`.
    categorical_enums: dict, optional
        A dictionary of all categories for the table columns containing categorical
        data. The categories will be made unique and sorted if they are not already.
        E.g. {'column_name': ['a', 'b'], 'other_column': ['c', 'd']}
    rasterize_function: function, optional
        Function to rasterize geometries. Other options are available in
        `geocube.rasterize`. Default is :func:`geocube.rasterize.rasterize_image`.

    Returns
    --------
    :obj:`xarray.Dataset`:
        Requested data in a :obj:`xarray.Dataset`.

    """
    geobox_maker = GeoBoxMaker(output_crs, resolution, align, geom, like)

    return VectorToCube(
        vector_data=vector_data,
        geobox_maker=geobox_maker,
        fill=fill,
        categorical_enums=categorical_enums,
    ).make_geocube(
        measurements=measurements,
        datetime_measurements=datetime_measurements,
        group_by=group_by,
        interpolate_na_method=interpolate_na_method,
        rasterize_function=rasterize_function,
    )
