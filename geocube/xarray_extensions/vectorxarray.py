# -- coding: utf-8 --
"""
This module is an extension for xarray to provide support for vector datasets.
"""
import geopandas as gpd
import xarray
from shapely.wkb import dumps, loads


def from_geodataframe(in_geodataframe):
    """
    Create an xarray object from a geodataframe.
    """
    geodf = in_geodataframe.copy().set_index("geometry")
    geox = xarray.Dataset.from_dataframe(geodf)
    geox.coords["crs"] = 0
    geox.coords["crs"].attrs = geodf.crs
    return geox


def open_dataset(*args, **kwargs):
    """
    Open the vxarray exported netCDF file as a Dataset.

    Returns
    -------
    :obj:`xarray.Dataset`

    """
    xds = xarray.open_dataset(*args, **kwargs)
    xds.coords["geometry"] = list(map(loads, xds.coords["geometry"].values))
    return xds


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
        out_obj = self._obj.drop("crs")
        extra_coords = list(set(list(out_obj.coords)) - {"geometry"})
        if extra_coords:
            out_obj = out_obj.copy().reset_coords(extra_coords)
        geodf = gpd.GeoDataFrame(out_obj.to_dataframe().reset_index())
        geodf.crs = self._obj.coords["crs"].attrs
        return geodf

    def to_netcdf(self, *args, **kwargs):
        """
        Write the data to a netCDF file.
        """
        out_obj = self._obj.copy()
        out_obj.coords["geometry"] = list(map(dumps, out_obj.coords["geometry"].values))
        out_obj.to_netcdf(*args, **kwargs)


@xarray.register_dataarray_accessor("vector")
class VectorArray(BaseVectorX):
    """This is the vector GIS extension for :class:`xarray.DataArray`"""

    def plot(self):
        self.to_geodataframe().plot(column=self._obj.name)


@xarray.register_dataset_accessor("vector")
class VectorDataset(BaseVectorX):
    """This is the vector GIS extension for :class:`xarray.Dataset`"""

    def plot(self, column):
        self._obj[column].vector.plot()
