import xarray as xr
import numpy as np
import pandas as pd
import sys
from datetime import datetime
from multiprocessing import Pool, Manager

mc, model = sys.argv[1], sys.argv[2]
month = sys.argv[3]

### settings ###

lmm = [40,90]
mstr = str(month).zfill(2)
lmm_str = str(lmm[0]) + 'N_' + str(lmm[1]) + 'N'

### load REF for dates ###

reference = xr.open_dataset('/users/jk/22/achereque/Paper2/L0_Reference/NSIDC_EASE2_N25km_v04.nc')

masks = {'Eur': xr.where(reference.lsmask==2, 1, 0).astype('int8'),
         'NAm': xr.where(reference.lsmask==1, 1, 0).astype('int8')}

# Reference snow is from NOAA CDR
# values are 2 if there is snow or 0 if there is no snow
reference['snow'] = xr.where(reference.land_ID==2,2,0) * xr.where((reference.latitude>=lmm[0])&(reference.latitude<=lmm[1]), 1 , 0)

### process data by threshold ###

fname = f'/users/jk/22/achereque/Paper2/L2_Processed_Vals/{mc}.{model}.reanalysis.weekly.swe.{mstr}.nc'

data = xr.open_dataset(fname)
data = xr.where((reference.latitude>=lmm[0])&(reference.latitude<=lmm[1]), data, np.nan)
print(data.nbytes)

#### placeholder datasets
both = xr.Dataset()
neither = xr.Dataset()
not_NOAA = xr.Dataset()
not_BTIM = xr.Dataset()

#### loop over thresholds
for threshold in np.arange(0.5, 18.5, 0.5):

    print(threshold, datetime.now().strftime("%H:%M:%S"), sep='\t')

    # subtract reference snow (values 2 or 0) and data (values 1 or 0) for each time step
    temp_ds = (reference['snow'] - xr.where(data.swe >= threshold, 1, 0)).astype('int8')
    print(temp_ds.nbytes)

    # for each region, count number of occurrences of each combination
    # if, after subtracting, the value is 1, they both had snow cover
    # if the value is 0, then neither had snow cover
    # if the value is -1, then NOAA had no snow but the BTIM dataset did
    # if the value is 2, then NOAA had snow but the BTIM dataset did not
    for region in ['Eur', 'NAm']:
        region_ds = temp_ds.sortby('time') * masks[region]

        both[str(int(10*threshold)).zfill(3)+'_'+region]  = xr.where(region_ds == 1, 1, 0).sum(('x', 'y'))
        neither[str(int(10*threshold)).zfill(3)+'_'+region] = xr.where(region_ds == 0, 1, 0).sum(('x', 'y'))
        not_NOAA[str(int(10*threshold)).zfill(3)+'_'+region] = xr.where(region_ds == -1, 1, 0).sum(('x', 'y'))
        not_BTIM[str(int(10*threshold)).zfill(3)+'_'+region] = xr.where(region_ds == 2, 1, 0).sum(('x', 'y'))

### After looping over thresholds, convert thresholds to a new dimension in the dataset
out_ds = xr.Dataset()
out_ds['both'] = both.to_array('threshold')
out_ds['neither'] = neither.to_array('threshold')
out_ds['not_NOAA'] = not_NOAA.to_array('threshold')
out_ds['not_BTIM'] = not_BTIM.to_array('threshold')

ds_Eur = out_ds.sel(threshold=[i for i in out_ds.threshold.values if 'Eur' in i])
ds_Eur['threshold'] = [float(i.split('_')[0])/10 for i in ds_Eur.threshold.values]

ds_NAm = out_ds.sel(threshold=[i for i in out_ds.threshold.values if 'NAm' in i])
ds_NAm['threshold'] = [float(i.split('_')[0])/10 for i in ds_NAm.threshold.values]

final_ds = xr.concat([ds_NAm, ds_Eur], pd.Index([1,2], name='region')).transpose('time', 'region', 'threshold')

# Save to file
final_ds.to_netcdf(f'/users/jk/22/achereque/Paper2/L3_Final/{mc}.{model}.reanalysis.weekly.scf_agreements.{lmm_str}.{mstr}.nc')

