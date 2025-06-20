# Download 

BrE5:https://doi.org/10.5683/SP3/HHIRBU

BrM2: https://doi.org/10.5683/SP3/C5I5HN

BrJ55: https://doi.org/10.5683/SP3/X5QJ3P

# Create directories

Each dataset should have its own directory. 
- L0_BTIM/ECWMF/ERA5
- L0_BTIM/NASA/MERRA2
- L0_BTIM/JMA/JRA55

# Modify coordinates and naming conventions after downloading:

Reorder coords:
```ncpdq -a time,latitude,longitude  ERA5_forced_swe_April_1983_1984.nc ERA5_forced_swe_April_1983_1984.reordered.nc```

Add units to lat/lon:
```ncatted -O -a units,longitude,a,c,degrees_east -a units,latitude,a,c,degrees_north ECMWF.ERA5.reanalysis.April.1983_1984.reordered.nc```

Subset area:
```cdo sellonlatbox,0,360,10,90 ECMWF.ERA5.reanalysis.April.1983_1984.reordered.nc ECMWF.ERA5.reanalysis.April.1983_1984.nc```

Calculate SWE:
```cdo -selvar,swe -expr,'swe=snow_depth*density' ECMWF.ERA5.reanalysis.April.1983_1984.nc L0_BTIM/ECMWF/ERA5/ECMWF.ERA5.reanalysis.April.1983_1984.nc```
