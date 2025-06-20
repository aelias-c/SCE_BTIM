#!/bin/bash

select_dates() {  

    local MC=$1; # argument 1
    local MODEL=$2; # argument 2

    local REF_FILE=$HOME/L0_Reference/NSIDC_EASE2_N25km_v04.nc;
    local IN_LOC=$HOME/L0_Regridding;
    local OUT_LOC=$HOME/L1_Minor_Processing;

    mkdir -p ${OUT_LOC}/${MC}/${MODEL};


    # For each month, subset files by selecting only the dates that appear in the NOAA CDR of SCE
    local idx=1;
    for m in Jan Feb March April May June July Aug Sept Oct Nov Dec; do
        echo $m;
        # Get the dates for month m
        local dates=$(cdo -s -showtimestamp -selmonth,${idx} -selyear,1979/2022 ${REF_FILE} | sed 's/^[ \t]*//' | perl -pe 's/  /,/g');

        echo $dates;

        # In parallel, select dates from each file and save to temporary file
        # Need cdo and gnu parallel for this task
        ls ${IN_LOC}/${MC}/${MODEL}/${MC}.${MODEL}.reanalysis.${m}.????_????.nc | parallel --joblog log_${MODEL}.txt cdo -w -select,date=${dates} {} ${OUT_LOC}/{/}.temp;

        idx=$((idx+1));
        echo "next idx = ${idx}";

    done

    # Merge all temporary files
    cdo -setreftime,1980-01-01,00:00,days -mergetime ${OUT_LOC}/${MC}.${MODEL}.reanalysis.*.????_????.nc.temp ${OUT_LOC}/${MC}/${MODEL}/${MC}.${MODEL}.reanalysis.NOAA_dates.nc;

    rm ${OUT_LOC}/${MC}.${MODEL}.*.nc.temp;
}

# Run for all three datasets

select_dates ECMWF ERA5
select_dates JMA JRA55
select_dates NASA MERRA2
