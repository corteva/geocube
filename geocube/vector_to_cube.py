# -- coding: utf-8 --
"""
geocube core conversion functionality
"""
import numpy
import pandas
import xarray
from rioxarray.rioxarray import DEFAULT_GRID_MAP, affine_to_coords

from geocube.geo_utils.geobox import load_vector_data
from geocube.logger import get_logger
from geocube.rasterize import rasterize_image


def _format_series_data(data_series):
    """
    The purpose of this function is to convert the series data into a rasterizeable
    format if possible.

    Parameters
    ----------
    data_series: :obj:`geopandas.GeoSeries`
        The series to be converted.

    Returns
    -------
    :obj:`geopandas.GeoSeries`: The series that was converted if possible.

    """
    if "datetime" in str(data_series.dtype):
        data_series = pandas.to_numeric(data_series).astype(numpy.float64)
        get_logger().warning(
            f"The series '{data_series.name}' was converted from a date to a number to "
            "rasterize the data. To load the data back in as a date, "
            "use 'pandas.to_datetime()'."
        )
    elif str(data_series.dtype) == "category":
        data_series = data_series.cat.codes
    return data_series


class VectorToCube:
    """
    Tool that facilitates converting vector data to raster data into
    an :obj:`xarray.DataFrame`.
    """

    def __init__(self, vector_data, geobox_maker, fill=None, categorical_enums=None):
        """
        Initialize the GeoCube class.

        Parameters
        ----------
        vector_data: str or :obj:`geopandas.GeoDataFrame`
            A file path to an OGR supported source or GeoDataFrame containing
            the vector data.
        geobox_maker: :obj:`geocube.geo_utils.geobox.GeoBoxMaker`
            The geobox for the grid to be generated from the vector data.
        fill: float, optional
            The value to fill in the grid with for nodata. Default is NaN.
        categorical_enums: dict, optional
            A dictionary of all categories for the table columns containing
            categorical data. The categories will be made unique and sorted
            if they are not already.
            E.g. {'column_name': ['a', 'b'], 'other_column': ['c', 'd']}

        """
        self._vector_data = load_vector_data(vector_data)
        self._geobox = geobox_maker.from_vector(self._vector_data)
        self._grid_coords = affine_to_coords(
            self._geobox.affine, self._geobox.width, self._geobox.height
        )
        self._fill = fill if fill is not None else numpy.nan
        if categorical_enums is not None:
            for column_name, categories in categorical_enums.items():
                category_type = pandas.api.types.CategoricalDtype(
                    categories=sorted(set(categories)) + ["nodata"]
                )
                self._vector_data[column_name] = self._vector_data[column_name].astype(
                    category_type
                )

        # define defaults
        self._rasterize_function = rasterize_image
        self._datetime_measurements = ()
        self._categorical_enums = {}

    def make_geocube(
        self,
        measurements=None,
        datetime_measurements=None,
        group_by=None,
        interpolate_na_method=None,
        rasterize_function=None,
    ):
        """
        Rasterize vector data into an ``xarray`` object.  Each measurement will be a
        data variable in the :class:`xarray.Dataset`.

        See the `xarray documentation <http://xarray.pydata.org>`_
        for usage of the :class:`xarray.Dataset` and :class:`xarray.DataArray` objects.

        Parameters
        ----------
        measurements: list(str), optional
            Attributes name or list of names to be included. If a list is specified,
            the measurements will be returned in the order requested.
            By default all available measurements are included.
        datetime_measurements: list(str), optional
            Attributes that are temporal in nature and should be converted to the
            datetime format. These are only included if listed in 'measurements'.
        group_by: str, optional
            When specified, perform basic combining/reducing of the data on this column.
        interpolate_na_method:  {‘linear’, ‘nearest’, ‘cubic’}, optional
            This is the method for interpolation to use to fill in the nodata with
            :meth:`scipy.interpolate.griddata`.
        rasterize_function: function, optional
            Function to rasterize geometries. Other options are available in
            `geocube.rasterize`. Default is `geocube.rasterize.rasterize_image`.

        Returns
        --------
        :class:`xarray.Dataset`:
            Requested data in a :class:`xarray.Dataset`.

        """
        self._rasterize_function = (
            rasterize_image if rasterize_function is None else rasterize_function
        )
        if measurements is None:
            measurements = self._vector_data.columns.tolist()
            measurements.remove("geometry")

        self._datetime_measurements = ()
        if datetime_measurements is not None:
            self._datetime_measurements = tuple(
                set(datetime_measurements) & set(measurements)
            )
        # reproject vector data to the projection of the output raster
        vector_data = self._vector_data.to_crs(self._geobox.crs.wkt)

        # convert to datetime
        for datetime_measurement in self._datetime_measurements:
            vector_data[datetime_measurement] = pandas.to_datetime(
                vector_data[datetime_measurement]
            ).astype("datetime64[ns]")

        # get categorical enumerations if they exist
        self._categorical_enums = {}
        for categorical_column in vector_data.select_dtypes(["category"]).columns:
            self._categorical_enums[categorical_column] = vector_data[
                categorical_column
            ].cat.categories

        # map the shape data to the grid
        if group_by:
            vector_data = vector_data.groupby(group_by)
            try:
                measurements.remove(group_by)
            except ValueError:
                pass

        return self._get_dataset(
            vector_data, measurements, group_by, interpolate_na_method
        )

    @staticmethod
    def _get_attrs(measurement_name, fill_value):
        """
        Get attributes for data array.

        Parameters
        ----------
        measurement_name: str
            The measurement name.
        fill_value: int or float
            The fill value.

        Returns
        -------
        dict: Dict with attributes for data array.
        """
        return dict(
            name=measurement_name,
            long_name=measurement_name,
            grid_mapping=DEFAULT_GRID_MAP,
            _FillValue=fill_value,
        )

    def _update_time_attrs(self, attrs, image_data):
        """
        Update attributes and nodata values for time grid.

        Parameters
        ----------
        attrs: dict
            Dict with attributes for data array.
        image_data: :obj:`numpy.ndarray`
            Array with image data.

        Returns
        -------
        dict: Dict with attributes for data array.
        """
        attrs["units"] = "seconds from 1970-01-01T00:00:00"
        attrs["_FillValue"] = 0
        image_data[image_data == self._fill] = 0.0

    def _get_dataset(self, vector_data, measurements, group_by, interpolate_na_method):
        """
        Parameters
        ----------
        vector_data: str or :obj:`geopandas.GeoDataFrame`
            A file path to an OGR supported source or GeoDataFrame containing
            the vector data.
        measurements: list(str), optional
            Attributes name or list of names to be included. If a list is specified,
            the measurements will be returned in the order requested.
            By default all available measurements are included.
        group_by: str, optional
            When specified, perform basic combining/reducing of the data on this column.
        interpolate_na_method:  {‘linear’, ‘nearest’, ‘cubic’}, optional
            This is the method for interpolation to use to fill in the nodata with
            :meth:`scipy.interpolate.griddata`.

        Returns
        --------
        :obj:`xarray.Dataset`:
            Requested data in a :obj:`xarray.Dataset`.

        """
        data_vars = {}
        for measurement in measurements:
            if group_by:
                grid_array = self._get_grouped_grid(
                    vector_data[[measurement, "geometry"]], measurement, group_by
                )
            else:
                grid_array = self._get_grid(
                    vector_data[[measurement, "geometry"]], measurement
                )
            if grid_array is not None:
                data_vars[measurement] = grid_array

        if group_by:
            self._grid_coords[group_by] = list(vector_data.groups.keys())

        out_xds = xarray.Dataset(data_vars=data_vars, coords=self._grid_coords)

        for categorical_measurement, categoral_enums in self._categorical_enums.items():
            enum_var_name = f"{categorical_measurement}_categories"
            cat_attrs = dict(out_xds[categorical_measurement].attrs)
            cat_attrs["categorical_mapping"] = enum_var_name
            out_xds[categorical_measurement].attrs = cat_attrs
            out_xds[enum_var_name] = categoral_enums

        out_xds.rio.write_crs(str(self._geobox.crs), inplace=True)
        out_xds.rio.write_coordinate_system(inplace=True)
        if interpolate_na_method is not None:
            return out_xds.rio.interpolate_na(method=interpolate_na_method)

        return out_xds

    def _get_grouped_grid(self, grouped_dataframe, measurement_name, group_by):
        """Retrieve the variable data to append to the ssurgo :obj:`xarray.Dataset`.
        This method is designed specifically to work on a dataframe that has
        been grouped.

        Parameters
        ----------
        grouped_dataframe: pandas GroupBy object
            A pandas dataframe in as a GroupBy object.
        measurement_name: str
            Attributes name or list of names to be included. If a list is specified,
            the measurements will be returned in the order requested.
            By default all available measurements are included.
        group_by: str
            When specified, perform basic combining/reducing of the data on this column.

        Returns
        -------
        tuple: Options needed to create an :obj:`xarray.DataArray`.

        """
        logger = get_logger()

        image_data = []
        df_group = None
        fill_value = self._fill
        for _, df_group in grouped_dataframe:
            fill_value = (
                self._fill
                if str(df_group[measurement_name].dtype) != "category"
                else -1
            )
            image = self._rasterize_function(
                geometry_array=df_group.geometry,
                data_values=_format_series_data(df_group[measurement_name]).values,
                geobox=self._geobox,
                grid_coords=self._grid_coords,
                fill=fill_value,
            )
            if image is None:
                logger.warning(
                    f"Skipping attribute {measurement_name} due to missing data..."
                )
                return None

            image_data.append(image)

        attrs = self._get_attrs(measurement_name, fill_value)
        image_data = numpy.array(image_data)
        # it was converted to numeric date value
        if df_group is not None and "datetime" in str(df_group[measurement_name].dtype):
            self._update_time_attrs(attrs, image_data)

        return (group_by, "y", "x"), image_data, attrs

    def _get_grid(self, dataframe, measurement_name):
        """Retrieve the variable data to append to the ssurgo :obj:`xarray.Dataset`
        from a regular :obj:`geopandas.GeoDataFrame`.

        Parameters
        ----------
        dataframe: :obj:`geopandas.GeoDataFrame`
            A geopandas GeoDataFrame object to rasterize.
        measurement_name: str
            Attributes name or list of names to be included. If a list is specified,
            the measurements will be returned in the order requested.
            By default all available measurements are included.

        Returns
        -------
        tuple: Options needed to create an :obj:`xarray.DataArray`.

        """
        logger = get_logger()
        fill_value = (
            self._fill if str(dataframe[measurement_name].dtype) != "category" else -1
        )
        image_data = self._rasterize_function(
            geometry_array=dataframe.geometry,
            data_values=_format_series_data(dataframe[measurement_name]).values,
            geobox=self._geobox,
            grid_coords=self._grid_coords,
            fill=fill_value,
        )
        if image_data is None:
            logger.warning(
                f"Skipping attribute {measurement_name} due to missing data..."
            )
            return None

        attrs = self._get_attrs(measurement_name, fill_value)

        # it was converted to numeric date value
        if "datetime" in str(dataframe[measurement_name].dtype):
            self._update_time_attrs(attrs, image_data)

        return ("y", "x"), numpy.array(image_data), attrs
