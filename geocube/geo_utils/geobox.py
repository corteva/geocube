"""
This module is for GIS related utility functions.
"""
import json
import os
from collections.abc import Iterable
from typing import Any, Optional, Union

import geopandas
import rioxarray  # noqa: F401 pylint: disable=unused-import
import shapely.geometry.base
import xarray
from odc.geo import resyx_, wh_
from odc.geo.crs import CRS
from odc.geo.geobox import GeoBox
from odc.geo.geom import Geometry
from shapely.geometry import box, mapping

from geocube.exceptions import VectorDataError
from geocube.logger import get_logger


def geobox_from_rio(xds: Union[xarray.Dataset, xarray.DataArray]) -> GeoBox:
    """This function retrieves the geobox using rioxarray extension.

    Parameters
    ----------
    xds: :obj:`xarray.DataArray` or :obj:`xarray.Dataset`
        The xarray dataset to get the geobox from.

    Returns
    -------
    :obj:`odc.geo.geobox.GeoBox`

    """
    height, width = xds.rio.shape
    try:
        transform = xds.rio.transform()
    except AttributeError:
        transform = xds[xds.rio.vars[0]].rio.transform()
    return GeoBox(
        shape=wh_(width, height),
        affine=transform,
        crs=CRS(xds.rio.crs.to_wkt()),
    )


def load_vector_data(
    vector_data: Union[str, os.PathLike, geopandas.GeoDataFrame]
) -> geopandas.GeoDataFrame:
    """
    Parameters
    ----------
    vector_data: str, path-like object or :obj:`geopandas.GeoDataFrame`
        A file path to an OGR supported source or GeoDataFrame containing
        the vector data.

    Returns
    -------
    :obj:`geopandas.GeoDataFrame` containing the vector data.

    """
    logger = get_logger()

    if isinstance(vector_data, (str, os.PathLike)):
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


class GeoBoxMaker:
    """
    This class is meant for delayed GeoBox making. Stores partial information until
    all information needed is obtained.
    """

    def __init__(
        self,
        output_crs: Any,
        resolution: Optional[Union[float, Iterable[float]]],
        align: Optional[tuple[float, float]],
        geom: Optional[Union[str, dict, shapely.geometry.base.BaseGeometry, Geometry]],
        like: Optional[Union[xarray.Dataset, xarray.DataArray]],
    ) -> None:
        """Get the geobox to use for the grid.

        Parameters
        ----------
        output_crs: Any, optional
            The CRS of the returned data.  If no CRS is supplied, the CRS of
             the stored data is used.
        resolution: Union[float, Iterable[float]], optional
            A tuple of the spatial resolution of the returned data.
            This includes the direction (as indicated by a positive or negative number).
            Typically when using most CRSs, the first number would be negative.
        align: tuple[float, float], optional
            Load data such that point 'align' lies on the pixel boundary.
            Units are in the co-ordinate space of the output CRS.
            Default is (0,0)
        geom: Union[str, dict, shapely.geometry.base.BaseGeometry, odc.geo.geom.Geometry], optional
            A GeoJSON string for the bounding box of the data.
        like: :obj:`xarray.Dataset` | :obj:`xarray.DataArray`, optional
            Uses the output of a previous ``load()`` to form the basis of a request for
            another product.

        """
        self.output_crs = output_crs
        self.resolution = (
            resolution if not isinstance(resolution, Iterable) else resyx_(*resolution)
        )
        self.align = None if align is None else resyx_(*align)

        if isinstance(geom, str):
            geom = json.loads(geom)
        self.geom = geom
        self.like = like

    def from_vector(
        self, vector_data: Union[str, os.PathLike, geopandas.GeoDataFrame]
    ) -> GeoBox:
        """Get the geobox to use for the grid.

        Parameters
        ----------
        vector_data: str, path-like object or :obj:`geopandas.GeoDataFrame`
            A file path to an OGR supported source or GeoDataFrame
            containing the vector data.

        Returns
        -------
        :obj:`odc.geo.geobox.GeoBox`
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
            except (AttributeError, ValueError):
                geobox = geobox_from_rio(self.like)
            return geobox

        if self.resolution is None:
            raise RuntimeError("Must specify 'resolution' if 'like' not specified.")

        if self.output_crs:
            crs = CRS(self.output_crs)
        else:
            crs = CRS(vector_data.crs)

        if self.geom is None and self.output_crs:
            geopoly = Geometry(
                mapping(box(*vector_data.to_crs(crs).total_bounds)),
                crs=crs,
            )
        elif self.geom is None:
            geopoly = Geometry(mapping(box(*vector_data.total_bounds)), crs=crs)

        else:
            crs_input = "EPSG:4326"
            if isinstance(self.geom, dict) and "crs" in self.geom:
                crs_input = self.geom["crs"]["properties"]["name"]
            geom_crs = CRS(crs_input)
            geopoly = Geometry(self.geom, crs=geom_crs)
        return GeoBox.from_geopolygon(geopoly, self.resolution, crs, self.align)
