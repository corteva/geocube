Getting Started
================

`geocube` combines the interfaces of:

- `geopandas <https://github.com/geopandas/geopandas>`__
- `xarray <https://github.com/pydata/xarray>`__
- `rioxarray <https://github.com/corteva/rioxarray>`__

and is powered by `GDAL <https://github.com/osgeo/gdal>`__ using:

- `rasterio <https://github.com/mapbox/rasterio>`__
- `fiona <https://github.com/toblerity/fiona>`__
- `datacube <https://github.com/opendatacube/datacube-core>`__


When getting started, the API documentation to start reading would be :func:`geocube.api.core.make_geocube`.

The simplest example would be to rasterize a single column:

.. code-block:: python

    from geocube.api.core import make_geocube

    out_grid = make_geocube(
        vector_data="path_to_file.gpkg",
        measurements=["column_name"],
        resolution=(-0.0001, 0.0001),
    )
    out_grid["column_name"].rio.to_raster("my_rasterized_column.tif")


You can also rasterize a `GeoDataFrame <https://geopandas.readthedocs.io/en/latest/docs/user_guide/data_structures.html#geodataframe>`__
directly in the `vector_data` argument. This enables you to `load in subsets of data <https://geopandas.readthedocs.io/en/latest/docs/user_guide/io.html#reading-subsets-of-the-data>`__
or perform various operations before rasterization.

Once finished, you can write to anything supported by `rasterio <https://github.com/mapbox/rasterio>`__
using `rioxarray`'s `rio.to_raster() <https://corteva.github.io/rioxarray/stable/examples/convert_to_raster.html>`__ method.
You can also write to a netCDF file using `xarray`'s `to_netcdf() <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html>`__.

However, life is only this simple when your data is perfectly clean, geospatially unique, and numeric.
The good news is that geocube supports a variety of use cases and custom rasterization functions if your dataset
does not meet these criteria (see: :ref:`usage_examples`).
