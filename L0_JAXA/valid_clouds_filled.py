import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st
import cartopy.crs as ccrs
import os

data = xr.open_dataset(os.environ['HOME'] + '/L0_JAXA/JAXA.JASMES.sce.nc')
data['y'] = ('y', list(reversed(data.y.values)))

ref = xr.open_dataset(os.environ['HOME'] + '/L0_Reference/NSIDC_EASE2_N25km_v04.nc')

mask = xr.where((ref.latitude>=40) & (ref.lsmask.isin([1,2])), 1., 0.)

drop_dates = (xr.where(data.Surface_Flag<255, 1., 0.) * mask).sum(('x','y')) < 72537
data.where(~drop_dates, drop=True).to_netcdf(os.environ['HOME'] + '/L0_JAXA/JAXA.JASMES.sce.valid_dates.nc')

valid_dates = xr.open_dataset(os.environ['HOME'] + '/L0_JAXA/JAXA.JASMES.sce.valid_dates.nc').Surface_Flag
valid_dates_update = valid_dates.copy(deep=True)

# Ensure time is sorted and extract numpy arrays for fast lookup
times = valid_dates_update.time.values
time_index = {t: idx for idx, t in enumerate(times)}

# Define 7-day timedelta
week = np.timedelta64(7, 'D')

# Loop through time indices (excluding first and last)
for i in range(1, len(times) - 1):
    current_time = times[i]
    prev_time = current_time - week
    next_time = current_time + week

    # Ensure both neighbors exist in the valid_dates_updateset
    if prev_time in time_index and next_time in time_index:
        # Get the indices
        prev_idx = time_index[prev_time]
        next_idx = time_index[next_time]

        # Extract snow masks
        prev_snow = np.isin(valid_dates_update[prev_idx, :, :], [2, 3])
        next_snow = np.isin(valid_dates_update[next_idx, :, :], [2, 3])
        current_cloud = valid_dates_update[i, :, :] == 1

        # Determine where to replace cloud with snow
        replace_mask = current_cloud & prev_snow & next_snow

        # Perform replacement
        updated_slice = valid_dates_update[i, :, :].values  # Get array
        updated_slice[replace_mask] = 2       # Replace cloud with snow
        valid_dates_update[i, :, :] = updated_slice         # Write back

valid_dates_update.to_netcdf("JAXA.JASMES.sce.final.nc")
