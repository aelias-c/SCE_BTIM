import xarray as xr

def subsample_weight_and_timeav_like_NOAA(indata, month, ylim = [1980, 2020],
                                          weights_loc='/users/jk/22/achereque/Paper2/L0_Reference/'):
    '''Apply weighting to weekly input data. Averages using NOAA dates only.

    Parameters
    ----------
    indata : xr.DataArray or xr.Dataset
        input data
    month : int or str
        month of interest
    ylim : list
        year limits to apply weighting from August ymin to July ymax. Default is [1980, 2020].
    '''
                                            
    mname = dict(zip(range(1, 13), ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']))
    inv_mname = dict(zip(['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], range(1, 13)))

    ### Load weekly weighting data
    weight_ds = xr.open_dataset(weights_loc + 'NOAA_like.weekly_weights.nc')
    
    ### Decode month and select it from weight_ds
    if type(month) == str:
        m_weights = weight_ds[month].dropna(dim='time')
        month_convert_num = inv_mname[month]
    elif type(month) == int:
        m_weights = weight_ds[mname[month]].dropna(dim='time')
        month_convert_num = month
    else:
        raise ValueError(r'month must be int or str in ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']')

    ### We care to group months by the water year they belong to, August-July
    ### Create a variable to hold the water year information for later grouping                                        
    m_weights['start_year'] = (('time'), [i.dt.year-1 if i.dt.month < 8 else i.dt.year for i in m_weights.time])

    ### Weights contributing to each snow year's average should add to one 
    m_weights = m_weights.groupby('start_year') / m_weights.groupby('start_year').sum() 

    ### Drop years outside bounds
    lower_lim = (m_weights.time.dt.year>ylim[0])|((m_weights.time.dt.month>=8)&(m_weights.time.dt.year==ylim[0]))
    upper_lim = (m_weights.time.dt.year<ylim[1])|((m_weights.time.dt.month<8)&(m_weights.time.dt.year==ylim[1]))

    m_weights = m_weights.where(upper_lim & lower_lim, drop=True).drop('start_year')

    ### Subset dates using NOAA validity time stamps
    m_weights['time'] = m_weights.time.indexes['time']
    subset_indata = indata.sel(time=indata.time.dt.date.isin(m_weights.time.dt.date), drop=True)

    ### Weight data and calculate monthly mean
    weighted_data = (subset_indata * m_weights).resample(time='YS-AUG').sum(dim='time')

    weighted_data = weighted_data.assign_coords(time=weighted_data.time.dt.year).rename({'time':'year'})

    if month < 8:
        weighted_data = weighted_data.assign_coords(year=weighted_data.year+1)

    weight_ds.close()

    return weighted_data

    
