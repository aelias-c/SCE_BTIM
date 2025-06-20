import numpy as np
from pyhdf.SD import SD, SDC
from pyproj import Transformer
from scipy.stats import mode
import xarray as xr
import os
import re
import sys
from collections import defaultdict
import pandas as pd

# === USER INPUT ===
HDF_FILE = os.path.join(sys.argv[1])
DATASET_NAME = 'Surface_Flag'

# === Step 0: Extract date info from filename ===
date_pattern = re.compile(r'(\d{8}_\d{8})')
basename = os.path.basename(HDF_FILE)
match = date_pattern.search(basename).group(1)
start_date_str, end_date_str = match.split('_')

start_date = pd.to_datetime(start_date_str, format='%Y%m%d')
end_date = pd.to_datetime(end_date_str, format='%Y%m%d')

output_nc = os.path.join(os.environ['HOME'], f'/L0_JAXA/scripts/weekly_processed/surface_flag.{match}.nc')

if not os.path.isfile(output_nc):
    # === Step 1: Read data ===
    hdf = SD(HDF_FILE, SDC.READ)
    data = hdf.select(DATASET_NAME)[:].astype(np.uint16)

    # Original data shape and grid info
    nrows, ncols = data.shape  # Should be (3601, 7200)

    # === Step 2: Construct lat/lon grid with correct extents ===
    lons = np.linspace(0.0, 359.95, ncols)        # 0 to 359.95E
    lats = np.linspace(90.0, -90.0, nrows)        # 90N to -90S (top to bottom)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # === Step 3: Remap categories ===
    remap = np.full_like(data, 255, dtype=np.uint8)

    remap[data == 10] = 1                          # Cloud over land
    remap[np.isin(data, [11, 13, 17])] = 2         # Dry snow or polar night
    remap[np.isin(data, [211, 213])] = 3           # Wet snow
    remap[data == 15] = 4                          # Land (non-snow)
    remap[data == 19] = 5                          # No data over land
    # Others remain 255

    # === Step 4: Projection transformer ===
    transformer = Transformer.from_crs('epsg:4326', 'epsg:6931', always_xy=True)
    flat_lon = lon_grid.flatten()
    flat_lat = lat_grid.flatten()
    src_x, src_y = transformer.transform(flat_lon, flat_lat)

    # === Step 5: Define target grid ===
    target_width = 720
    target_height = 720
    cell_size = 25000  # meters

    xmin, ymin, xmax, ymax = -9000000.0, -9000000.0, 9000000.0, 9000000.0

    # === Step 6: Bin source points to EASE2 grid ===
    bin_x = ((src_x - xmin) // cell_size).astype(int)
    bin_y = ((src_y - ymin) // cell_size).astype(int)
    valid_mask = (bin_x >= 0) & (bin_x < target_width) & (bin_y >= 0) & (bin_y < target_height)

    bin_x = bin_x[valid_mask]
    bin_y = bin_y[valid_mask]
    source_values = remap.flatten()[valid_mask]

    # === Step 7: Aggregate using mode ===
    target_array = np.full((target_height, target_width), 255, dtype=np.uint8)
    bins = defaultdict(list)
    for x_idx, y_idx, val in zip(bin_x, bin_y, source_values):
        if val != 255:
            bins[(y_idx, x_idx)].append(val)

    for (y_idx, x_idx), vals in bins.items():
        if vals:
            target_array[y_idx, x_idx] = mode(vals).mode

    # === Step 8: Create xarray Dataset with time ===
    x_coords = np.linspace(xmin + cell_size / 2, xmax - cell_size / 2, target_width)
    y_coords = np.linspace(ymax - cell_size / 2, ymin + cell_size / 2, target_height)
    time_coord = [end_date]

    flag_descriptions = '''
    1 : Cloud over land
    2 : Dry snow over land or polar night over land
    3 : Wet snow over land
    4 : Land (non-snow)
    5 : No data (over land)
    255 : Fill / no data
    '''

    ds = xr.Dataset(
        {
            'Surface_Flag': (('time', 'y', 'x'), target_array[np.newaxis, :, :])
        },
        coords={
            'time': time_coord,
            'x': x_coords,
            'y': y_coords
        },
        attrs={
            'description': 'Surface_Flag resampled to EASE2 25km grid',
            'source_file': basename,
            'time_coverage_start': start_date.strftime('%Y-%m-%d'),
            'time_coverage_end': end_date.strftime('%Y-%m-%d')
        }
    )

    ds.Surface_Flag.attrs['units'] = 'category'
    ds.Surface_Flag.attrs['long_name'] = 'Grouped cloud and surface classification flags'
    ds.Surface_Flag.attrs['missing_value'] = 255
    ds.Surface_Flag.attrs['_FillValue'] = 255
    ds.Surface_Flag.attrs['flag_descriptions'] = flag_descriptions

    # === Step 9: Save NetCDF ===
    ds.to_netcdf(output_nc)
    print(f'Saved resampled data to {output_nc}')

else:
    print('EXISTS:', output_nc, sep='\t')
