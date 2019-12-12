History
=======

0.0.10
------
- Added filter_nan kwarg to filter out missing data when rasterizing (issue #9)
- Change default fill value to NaN when rasterizing (pull #11)

0.0.9
-----
- Added `rescale` kwarg to `geocube.rasterize.rasterize_points_griddata`. (pull #8)
- Removed `fillna(numpy.nan)` in `geocube.geo_utils.geobox.load_vector_data` as not necessary
  and for compatibility with `geopandas==0.6.0`. (pull #8)

0.0.8
-----
- Add merge algorithm option for rasterization (issue #5)
- Drop Python 2 support (issue #6)

0.0.7
-----
- Remove geocube pin (pull #4)

0.0.6
-----
- Added additional methods for resampling points to a 2D grid (pull #3)

0.0.5
-----
- Fix converting to another projection to ensure bounds are correctly accounted for (pull #2)
