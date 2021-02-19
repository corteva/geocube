# -- coding: utf-8 --
"""
This module is for GIS related utility functions.
"""
import json
from distutils.version import LooseVersion

import geopandas
import rioxarray  # noqa: F401 pylint: disable=unused-import
from datacube.utils import geometry
from shapely.geometry import box, mapping

from geocube.exceptions import VectorDataError
from geocube.logger import get_logger

try:
    from rioxarray.crs import crs_to_wkt
except ImportError:
    # rioxarray 0.3+
    from rioxarray.crs import crs_from_user_input

    def crs_to_wkt(input_crs):
        """
        Convert CRS input to WKT format
        """
        return crs_from_user_input(input_crs).to_wkt()


def geobox_from_rio(xds):
    """This function retrieves the geobox using rioxarray extension.

    Parameters
    ----------
    xds: :obj:`xarray.DataArray` or :obj:`xarray.Dataset`
        The xarray dataset to get the geobox from.

    Returns
    -------
    :obj:`datacube.utils.geometry.GeoBox`

    """
    width, height = xds.rio.shape
    try:
        transform = xds.rio.transform()
    except AttributeError:
        transform = xds[xds.rio.vars[0]].rio.transform()
    return geometry.GeoBox(
        width=width,
        height=height,
        affine=transform,
        crs=geometry.CRS(crs_to_wkt(xds.rio.crs)),
    )


def load_vector_data(vector_data):
    """
    Parameters
    ----------
    vector_data: str or :obj:`geopandas.GeoDataFrame`
        A file path to an OGR supported source or GeoDataFrame containing
        the vector data.

    Returns
    -------
    :obj:`geopandas.GeoDataFrame` containing the vector data.

    """
    logger = get_logger()

    if isinstance(vector_data, str):
        vector_data = geopandas.read_file(vector_data)
    elif not isinstance(vector_data, geopandas.GeoDataFrame):
        vector_data = geopandas.GeoDataFrame(vector_data)

    if vector_data.empty:
        raise VectorDataError("Empty GeoDataFrame.")
    if "geometry" not in vector_data.columns:
        raise VectorDataError(
            "'geometry' column missing. Columns in file: "
            f"{vector_data.columns.values.tolist()}"
        )

    # make sure projection is set
    if not vector_data.crs:
        vector_data.crs = "EPSG:4326"
        logger.warning(
            "Projection not defined in `vector_data`."
            " Setting to geographic (EPSG:4326)."
        )
    return vector_data


def _datacube_to_geopandas_crs(dc_crs):
    """
    This gets the best representation of the datacube CRS object
    to be used by geopandas

    Parameters
    ----------
    dc_crs: :class:`datacube.utils.geometry.CRS`
        Input datacube CRS

    Returns
    -------
    str:
        Representation of CRS for geopandas.
    """
    # pylint: disable=protected-access
    if LooseVersion(geopandas.__version__) >= LooseVersion("0.6.0"):
        # this version of geopandas uses always_xy=True so WKT version is safe
        try:
            geo_crs = dc_crs.to_wkt()
        except AttributeError:
            geo_crs = dc_crs.wkt
    else:
        try:
            # datacube version < 0.8 uses osgeo.osr SpatialReference
            geo_crs = dc_crs._crs.ExportToProj4()
        except AttributeError:
            # datacube version 0.8+ uses pyproj.CRS
            geo_crs = dc_crs._crs.to_proj4()
    return geo_crs


class GeoBoxMaker:
    """
    This class is meant for delayed GeoBox making. Stores partial information until
    all information needed is obtained.
    """

    def __init__(self, output_crs, resolution, align, geom, like):
        """Get the geobox to use for the grid.

        Parameters
        ----------
        output_crs: str, optional
            The CRS of the returned data.  If no CRS is supplied, the CRS of
             the stored data is used.
        resolution: (float,float), optional
            A tuple of the spatial resolution of the returned data.
            This includes the direction (as indicated by a positive or negative number).
            Typically when using most CRSs, the first number would be negative.
        align: (float,float), optional
            Load data such that point 'align' lies on the pixel boundary.
            Units are in the co-ordinate space of the output CRS.
            Default is (0,0)
        geom: str, optional
            A GeoJSON string for the bounding box of the data.
        like: :obj:`xarray.Dataset`, optional
            Uses the output of a previous ``load()`` to form the basis of a request for
            another product.

        """
        self.output_crs = output_crs
        self.resolution = resolution
        self.align = align
        self.geom = geom
        self.like = like

    def from_vector(self, vector_data):
        """Get the geobox to use for the grid.

        Parameters
        ----------
        vector_data: str or :obj:`geopandas.GeoDataFrame`
            A file path to an OGR supported source or GeoDataFrame
            containing the vector data.

        Returns
        -------
        :obj:`datacube.utils.geometry.GeoBox`
            The geobox for the grid to be generated from the vector data.

        """
        vector_data = load_vector_data(vector_data)

        if self.like is not None:
            assert (
                self.output_crs is None
            ), "'like' and 'output_crs' are not supported together"
            assert (
                self.resolution is None
            ), "'like' and 'resolution' are not supported together"
            assert self.align is None, "'like' and 'align' are not supported together"
            try:
                geobox = self.like.geobox
            except AttributeError:
                geobox = geobox_from_rio(self.like)
            return geobox

        if self.resolution is None:
            raise RuntimeError("Must specify 'resolution' if 'like' not specified.")

        if self.output_crs:
            crs = geometry.CRS(crs_to_wkt(self.output_crs))
        else:
            crs = geometry.CRS(crs_to_wkt(vector_data.crs))

        if self.geom is None and self.output_crs:
            geopoly = geometry.Geometry(
                mapping(
                    box(
                        *vector_data.to_crs(
                            _datacube_to_geopandas_crs(crs)
                        ).total_bounds
                    )
                ),
                crs=crs,
            )
        elif self.geom is None:
            geopoly = geometry.Geometry(
                mapping(box(*vector_data.total_bounds)), crs=crs
            )

        else:
            geom_json = json.loads(self.geom)
            geom_crs = geometry.CRS(
                geom_json["crs"]["properties"]["name"]
                if "crs" in geom_json
                else "epsg:4326"
            )

            geopoly = geometry.Geometry(geom_json, crs=geom_crs)

        return geometry.GeoBox.from_geopolygon(
            geopoly, self.resolution, crs, self.align
        )
