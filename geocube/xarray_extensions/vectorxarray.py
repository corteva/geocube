# -- coding: utf-8 --
"""
This module is an extension for xarray to provide support for vector datasets.
"""
import geopandas as gpd
import numpy
import rioxarray  # noqa: F401 pylint: disable=unused-import
import xarray
from shapely.wkb import dumps, loads

dumps_v = numpy.vectorize(dumps)
loads_v = numpy.vectorize(loads)


def from_geodataframe(in_geodataframe):
    """
    Create an xarray object from a geodataframe.
    """
    # pylint: disable=protected-access
    geodf = in_geodataframe.copy().set_index("geometry")
    geox = xarray.Dataset.from_dataframe(geodf)
    # hack to get around dimension error when
    # writing CRS
    geox.rio._x_dim = "x"
    geox.rio._y_dim = "y"
    geox.rio.write_crs(geodf.crs, inplace=True)
    geox.rio._x_dim = None
    geox.rio._y_dim = None
    return geox


def open_dataset(*args, **kwargs):
    """
    Open the vxarray exported netCDF file as a Dataset.

    Returns
    -------
    :obj:`xarray.Dataset`

    """
    xds = xarray.open_dataset(*args, **kwargs)
    return xds.assign_coords(geometry=loads_v(xds.coords["geometry"].values))


class BaseVectorX:
    """This is the base for the vector GIS extension."""

    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def _validate_operation(self):
        if set(self._obj.dims) - {"geometry"}:
            raise ValueError(
                "Extra dimensions found. Please slice/squeeze data"
                " so that the only dimension is 'geometry'."
            )

    def to_geodataframe(self):
        """
        Convert to a GeoDataFrame.

        Returns
        -------
        :obj:`geopandas.GeoDataFrame`

        """
        self._validate_operation()
        out_obj = self._obj.drop_vars(self._obj.rio.grid_mapping)
        extra_coords = list(set(list(out_obj.coords)) - {"geometry"})
        if extra_coords:
            out_obj = out_obj.copy().reset_coords(extra_coords)
        geodf = gpd.GeoDataFrame(out_obj.to_dataframe().reset_index())
        geodf.crs = self._obj.rio.crs
        return geodf

    def to_netcdf(self, *args, **kwargs):
        """
        Write the data to a netCDF file.
        """
        self._obj.assign_coords(
            geometry=dumps_v(self._obj.coords["geometry"].values)
        ).to_netcdf(*args, **kwargs)


@xarray.register_dataarray_accessor("vector")
class VectorArray(BaseVectorX):
    """This is the vector GIS extension for :class:`xarray.DataArray`"""

    def plot(self, *args, **kwargs):
        """
        Helper method to plot the geometry data via geopandas.

        Parameters
        ----------
        *args, **kwargs:
            Arguments to pass to the plot call.
        """
        self.to_geodataframe().plot(column=self._obj.name, *args, **kwargs)


@xarray.register_dataset_accessor("vector")
class VectorDataset(BaseVectorX):
    """This is the vector GIS extension for :class:`xarray.Dataset`"""

    def plot(self, column, *args, **kwargs):
        """
        Helper method to plot the geometry data via geopandas.

        Parameters
        ----------
        column: str
            The name of the column (variable) to plot.
        *args, **kwargs:
            Arguments to pass to the plot call.
        """
        self._obj[column].vector.plot(*args, **kwargs)
