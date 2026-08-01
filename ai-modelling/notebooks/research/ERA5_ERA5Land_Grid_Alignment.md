# ERA5 and ERA5-Land Grid Alignment Verification

## Purpose

This verification checks whether the January 2018 ERA5 and ERA5-Land exports use matching grid-cell geometries and matching 12-hour timestamps. 

The full verification code is available in: 
`verify_era5_era5land_grid_alignemnt.ipynb`

## Method

This notebook: 
- compares the original `grid_id` sets
- checks whether each `grid_id` maps to one or multiple geometries
- standardises the `.geo` polygon values
- creates temporary geometry hashes for comparison
- compares all unique polygon geometries
- compares all geometry-datetime combinations

## Results
- ERA5 unique geometries: 14,258
- ERA5-Land unique geometries: 14,258
- Geometries only in ERA5: 0
- Geometries only in ERA5-Land: 0
- Geometry sets matched: Yes
- Geometry and datetime combinations matched: Yes

## Conclusion

The January 2018 ERA5 and ERA5-Land exports contain matching grid-cell geometries and matching 12-hour timestamps. 

## Important Finding
The existing `grid_id` values should not be used alone as unique spatial identifiers because one `grid_id` can be associated with multiple geometries. 

The `.geo` polygon field should be treated as the source of truth for spatial alignment. 

For future merging, the team should use a stable spatial identifiers derived from the geometry, together with `datetime`.

