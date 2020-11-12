# -- coding: utf-8 --
"""
The CLI interface to the load module for GeoCube
"""

import click
import numpy
import xarray

from geocube.api import core


@click.command(name="make-geocube")
@click.option(
    "-i",
    "--interpolate-na-method",
    help="This is the method for interpolation to use to fill in the nodata.",
    type=click.Choice(["linear", "nearest", "cubic"]),
    required=False,
)
@click.option(
    "-gb",
    "--group-by",
    help="When specified, perform basic combining/reducing of the data on this column.",
    required=False,
)
@click.option(
    "-f",
    "--fill",
    type=float,
    help="The value to fill in the grid with for nodata. Default is NaN.",
    default=numpy.nan,
    required=False,
)
@click.option(
    "-l",
    "--like",
    type=click.Path(exists=True),
    help="Uses the netCDF file output of a previous ``load()`` "
    "to form the basis of a request for another product.",
    required=False,
)
@click.option(
    "-g",
    "--geom",
    help="GeoJSON string for the bounding box of the data used to construct the grid.",
    required=False,
)
@click.option(
    "-a",
    "--align",
    nargs=2,
    type=float,
    help=(
        "Load data such that point 'align' lies on the pixel boundary."
        " Default is (0, 0)."
    ),
    required=False,
)
@click.option(
    "-r",
    "--resolution",
    nargs=2,
    type=float,
    help="A tuple of the spatial resolution of the returned data. Ex. -r -10 10.",
    required=False,
)
@click.option(
    "-c",
    "--output-crs",
    help=(
        "The CRS of the returned data. (e.g. epsg:4326). "
        "If no CRS is supplied, the CRS of the input data is used."
    ),
    required=False,
)
@click.option(
    "-m",
    "--measurements",
    help="Measurement subset to load in.",
    multiple=True,
    required=False,
)
@click.argument("vector_data", type=click.Path(exists=True), required=True)
@click.argument("output_file", required=True)
def make_geocube(
    output_file,
    vector_data,
    measurements,
    output_crs,
    resolution,
    align,
    geom,
    like,
    fill,
    group_by,
    interpolate_na_method,
):
    """
    Utility to load vector data into the xarray raster format.
    """
    if not resolution and isinstance(resolution, tuple):
        resolution = None
    if not align and isinstance(align, tuple):
        align = None
    if not measurements and isinstance(measurements, tuple):
        measurements = None

    if like is not None:
        like = xarray.open_dataset(like)
    try:
        gcds = core.make_geocube(
            vector_data=vector_data,
            measurements=measurements,
            output_crs=output_crs,
            resolution=resolution,
            align=align,
            geom=geom,
            like=like,
            fill=fill,
            group_by=group_by,
            interpolate_na_method=interpolate_na_method,
        )
    finally:
        if like is not None:
            like.close()

    gcds.to_netcdf(output_file)
