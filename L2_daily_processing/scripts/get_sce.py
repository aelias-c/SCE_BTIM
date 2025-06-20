import xarray as xr
import numpy as np
import os
import sys

# Open datasets
grid_data = xr.open_dataset(os.path.join(os.environ['HOME'], '/L0_Reference/NSIDC_EASE2_N25km_v04.nc'))

input_file = sys.argv[-1]

data = xr.open_dataset(input_file)
filename = os.path.basename(input_file)
basename, _ = os.path.splitext(filename)

# Latitude limits
lmm = [40, 90]

outloc = os.path.join(os.environ['SCRATCH'], '/L2_daily_thresholding/', basename+'.daily_SCE.40N_90N.nc')

# Create mask: land and latitude bounds
mask = xr.where(
    ((grid_data.lsmask == 1)| (grid_data.lsmask == 2)) &
    (grid_data.latitude <= lmm[1]) &
    (grid_data.latitude >= lmm[0]),
    1, 0
)
# Define thresholds array
thresholds = np.arange(0, 18.5, 0.5)

# Add threshold dim to thresholds array
threshold_da = xr.DataArray(thresholds, dims='threshold')

# First, align dims if needed:
try:
    swe = data.sd.transpose('time', 'x', 'y')
except AttributeError:
    print(input_file)

swe_expanded = swe.expand_dims(threshold=thresholds.size)
comparison = (swe_expanded > threshold_da)

# Apply mask, which has dims (x,y)
mask_expanded = mask.expand_dims({'time': swe.time.size, 'threshold': thresholds.size}).transpose('time', 'x', 'y', 'threshold')

masked = comparison * mask_expanded  # still boolean but multiplied by 0 or 1 mask

# Calculate area per grid cell (25 km * 25 km in sq km)
area_km2 = 25 * 25 / 1e6  # in million sq km

# Sum over spatial dims (x,y)
result = masked.sum(dim=['x', 'y']) * area_km2  # dims: time, threshold

# Rename threshold dimension to string labels like '000mm', '005mm', ...
threshold_labels = [f"{int(t*10):03d}mm" for t in thresholds]

# Convert to Dataset with variables per threshold:
result = result.assign_coords(threshold=thresholds)
data_vars = {label: result.sel(threshold=t, drop=True) for label, t in zip(threshold_labels, thresholds)}
result_ds = xr.Dataset(data_vars)

print('saving to >>>', outloc)

result_ds.to_netcdf(outloc)

