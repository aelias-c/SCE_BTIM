#!/bin/bash

REF_GRID=$HOME/L0_Reference/NSIDC_EASE2_N25km_v04.nc

MC=${1} # first argument, modelling centre
MODEL=${2} # second argument, model

# Create new directory if one doesn't exist for the model
mkdir -p $HOME/${MC}/${MODEL}

# Directories
DATA_LOC=$HOME/L0_BTIM/${MC}/${MODEL}
OUTLOC=$HOME/L0_Regridding/${MC}/${MODEL}

### Conservative regridding
# list files and then, in parallel, remap with first order conservative method
# (need cdo installed to run this)
# Additional steps: 
# select only latitudes from 10-90N to save space,
# convert longitudes to range -180 to 180,
# calculate SWE by multiplying density and snow depth from BTIM data
# save to file

ls -r ${DATA_LOC}/*.nc | parallel --jobs 30 --joblog log_${MODEL}.txt --delay 0.25 cdo -remapcon,${REF_GRID} -sellonlatbox,-180.,180.,10.,90. -selvar,swe -expr,'swe=density*snow_depth' {} ${OUTLOC}/{/}
