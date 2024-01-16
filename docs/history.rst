History
=======

Latest
-------
- BUG: Update minimize dtype for int64 & int8 support (issue #139)
- BUG: Support pandas IntegerArray (pull #158)

0.4.2
-------
- BUG: Fix conversion to datetime64[ns] for naive datetimes (pull #145)

0.4.1
-------
- BUG: Fix conversion to datetime64[ns] (pull #143)
- BUG: Fix :func:`geocube.vector.vectorize` when nodata is None (pull #142)

0.4.0
-------
- DEP: Drop Python 3.8 Support (issue #136)
- ENH: Add :func:`geocube.vector.vectorize` (issue #65)

0.3.3
------
- BUG: Allow resolution in list format (pull #122)

0.3.2
------
- MNT: corrections to setup.cfg; use "pytest"; add "make dist" target (pull #111)
- BUG: Write transform on output dataset (pull #112)

0.3.1
------
- TYPE: Modified NDArray import for typing (pull #106)

0.3.0
-------
- BUG: Handle input CRS without EPSG (pull #105)
- TYPE: Added type hints (pull #101)

0.2.0
-------
- DEP: Replace datacube with odc-geo (issue #90)

0.1.2
------
- BUG: Fix width and height order to the one used in rioxarray (issue #93)

0.1.1
-------
- DEP: Drop Python 3.7 Support (issue #86)
- BUG: Updated logic to skip rasterizing strings for numpy 1.22+ (issue #88)

0.1.0
------
- ENH: Minimize dtype when possible in `geocube.rasterize.rasterize_image` (issue #72)
- REF: remove unnecessary shapely.geometry.mapping in rasterize_image (#80)
- ENH: `vector_data` to read path-like objects (pull #81)

0.0.18
------
- DEP: Explicitly add scipy as dependency (pull #75)

0.0.17
------
- DEP: Python 3.7+ (#67)
- REF: Write grid_mapping to encoding instead of attrs (#66)

0.0.16
------
- BUG: Compatibility with rioxarray 0.3 (#57)

0.0.15
------
- Address xarray & numpy deprecations (#43)

0.0.14
------
- Add "all_touched" keyword argument to geocube.rasterize.rasterize_image (pull #40)

0.0.13
------
- Address deprecation warnings from datacube and rioxarray (issue #29)

0.0.12
------
- ENH: Added :func:`geocube.show_versions` and cli `geocube --show-versions` (pull #23)
- Add compatibility between datacube and geopandas CRS versions (pull #24)

0.0.11
------
- Drop Python 3.5 Support (issue #12)
- ENH: Update to support geopandas with pyproj.CRS (pull #18)
- BUG: Update timestamp handling to ensure correct format for dtype (pull #18)

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
