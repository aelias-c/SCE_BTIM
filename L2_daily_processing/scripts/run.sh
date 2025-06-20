#!/bin/bash


get_sce_daily() {
    local MC=$2
    local MODEL=$2
    data_loc=$HOME/L1_Regridded_Data
    lsmask_loc=$HOME/L0_Reference/NSIDC_EASE2_N25km_v04.nc

    ls -r $data_loc/$MC/$MODEL/$MC*nc | parallel --tmpdir ./scripts/tmp -j 20 --wd $PWD python $HOME/L2_daily_thresholding/scripts/get_sce.py {}
}


get_sce_daily ECMWF ERA5 #btim
get_sce_daily JMA JRA55 #btim
get_sce_daily NASA MERRA2 #btim
#get_sce_daily MERRA2 MERRA2
#get_sce_daily ECMWF ERA5Land

