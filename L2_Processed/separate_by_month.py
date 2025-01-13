import xarray as xr
import sys
from datetime import datetime
import numpy as np
mc, model = sys.argv[1], sys.argv[2]

weight_ds = xr.open_dataset('/users/jk/22/achereque/Paper2/L0_Reference/NOAA_like.weekly_weights.nc')
weight_ds = weight_ds.where(weight_ds.time.dt.year >= 1980, drop=True).sortby('time')
mname = dict(zip(range(1, 13), ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']))

data = xr.open_dataset(f'/users/jk/22/achereque/Paper2/L1_Minor_Processing/{mc}/{model}/{mc}.{model}.reanalysis.NOAA_dates.nc').swe

for m in [9,10,11,12,1,2,3,4,5,6]:

    print(mname[m], datetime.now().strftime("%H:%M:%S"), sep='\t')
    mstr=str(m).zfill(2)

    ref_times = weight_ds[mname[m]].dropna(dim='time').time
    print(ref_times.values[:5])

    # Select subset of dates using NOAA validity times that contribute to month m's average
    subset = data.where(data.time.isin(ref_times), drop=True).to_dataset(name='swe')
    print(subset.time[:5])

    subset['swe'].attrs['units'] = 'kg/m2'
    subset['swe'].attrs['long_name'] = 'snow water equivalent'
    subset['swe'].attrs['standard_name'] = 'liquid_water_content_of_surface_snow'
    
    subset.coords['crs'] = xr.Variable((), 0)
    subset.coords['crs'].attrs = dict(
                                        grid_mapping_name="lambert_azimuthal_equal_area",
                                        false_easting = 0.,
                                        false_northing = 0.,
                                        latitude_of_projection_origin = 90.,
                                        longitude_of_projection_origin = 0.,
                                        long_name = 'NSIDC_NH_EASE2_25km',
                                        longitude_of_prime_meridian = 0.,
                                        semi_major_axis = 6378137.,
                                        inverse_flattening = 298.257223563,
                                        GeoTransform = "-9000000 25000 0 9000000 0 -25000",
                                        )

    subset.attrs['title'] = f'Regridded B-TIM offline swe output for {mc}.{model} to the NSIDC NH EASE-Grid V2.'
    subset.attrs['summary'] = 'Subset of full time series using dates that appear in the Rutgers SCE dataset' +\
                                 f'and which contribute some weight (part of the preceeding week) to the month={mname[m]}.'
    
    subset.to_netcdf(f'/users/jk/22/achereque/Paper2/L2_Processed_Vals/{mc}.{model}.reanalysis.weekly.swe.{mstr}.nc')
