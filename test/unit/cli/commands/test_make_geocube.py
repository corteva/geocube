import os

import pytest
import xarray
from click.testing import CliRunner
from mock import patch

from geocube.cli.geocube import geocube
from test.conftest import TEST_COMPARE_DATA_DIR, TEST_INPUT_DATA_DIR


def _get_called_dict(**kwargs):
    default = dict(
        align=None,
        fill=None,
        geom=None,
        group_by=None,
        interpolate_na_method=None,
        like=None,
        measurements=None,
        output_crs=None,
        resolution=None,
        vector_data=os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"),
    )
    default.update(**kwargs)
    return default


INPUT_GEOM = (
    '{"type": "Polygon", "coordinates": '
    "[[[50.5, 50.0], [50.5, 50.5], [50.0, 50.5], [50.0, 50.0], [50.5, 50.0]]]}"
)
LIKE_PATH = os.path.join(TEST_COMPARE_DATA_DIR, "soil_grid_flat.nc")


@pytest.mark.parametrize(
    "params, called_with",
    [
        (
            ["-m", "measure1", "--measurements", "measure2"],
            _get_called_dict(measurements=("measure1", "measure2")),
        ),
        (["-c", "+init=epsg:4326"], _get_called_dict(output_crs="+init=epsg:4326")),
        (
            ["--output-crs", "+init=epsg:4326"],
            _get_called_dict(output_crs="+init=epsg:4326"),
        ),
        (["-r", "-10", "10"], _get_called_dict(resolution=(-10, 10))),
        (["--resolution", "-10", "10"], _get_called_dict(resolution=(-10, 10))),
        (["-a", "-10", "10"], _get_called_dict(align=(-10, 10))),
        (["--align", "-10", "10"], _get_called_dict(align=(-10, 10))),
        (["-g", INPUT_GEOM], _get_called_dict(geom=INPUT_GEOM)),
        (["--geom", INPUT_GEOM], _get_called_dict(geom=INPUT_GEOM)),
        (
            ["-l", LIKE_PATH],
            _get_called_dict(like=xarray.open_dataset(LIKE_PATH, autoclose=True)),
        ),
        (
            ["--like", LIKE_PATH],
            _get_called_dict(like=xarray.open_dataset(LIKE_PATH, autoclose=True)),
        ),
        (["-f", "-10"], _get_called_dict(fill=-10)),
        (["--fill", "-10"], _get_called_dict(fill=-10)),
        (["-gb", "attr"], _get_called_dict(group_by="attr")),
        (["--group-by", "attr"], _get_called_dict(group_by="attr")),
        (["-i", "nearest"], _get_called_dict(interpolate_na_method="nearest")),
        (
            ["--interpolate-na-method", "nearest"],
            _get_called_dict(interpolate_na_method="nearest"),
        ),
    ],
)
@patch("geocube.cli.commands.make_geocube.make_geocube")
def test_make_geocube_params(make_geocube_mock, params, called_with):
    with patch("geocube.cli.commands.make_geocube.click.Path"):
        cmd_out = CliRunner().invoke(
            geocube,
            [
                "make-geocube",
                os.path.join(TEST_INPUT_DATA_DIR, "soil_data_flat.geojson"),
                "outfile.nc",
            ]
            + params,
        )
    try:
        make_geocube_mock.assert_called_with(**called_with)
        make_geocube_mock().to_netcdf.assert_called_with("outfile.nc")
    except AssertionError:
        print(cmd_out.output)
        raise
