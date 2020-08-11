# %% imports
import os

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from scipy import interpolate

import config as cfg
from logging_config import setup_logging
from src.tools.data_processing import download_era_temp, days_in_year, medea_path

setup_logging()

# data is generated using Copernicus Climate Change Service Information
# Dataset citation: Copernicus Climate Change Service (C3S) (2019): C3S ERA5-Land reanalysis.
# Copernicus Climate Change Service, _date of access_. https://cds.climate.copernicus.eu/cdsapp#!/home

# ======================================================================================================================
# %% download era5 temperature (2 m) data

YEARS = range(2012, 2019, 1)
COUNTRY = {'AT': 'Austria', 'DE': 'Germany'}
ERA_DIR = medea_path('data', 'raw', 'era5')
PPLANT_DB = medea_path('data', 'processed', 'power_plant_db.xlsx')

# format for downloading ERA5: north/west/south/east
BBOX_CWE = [59.8612, -10.8043, 35.8443, 30.3285]

for year in YEARS:
    filename = os.path.join(ERA_DIR, f'temperature_europe_{year}.nc')
    download_era_temp(filename, year, BBOX_CWE)

# ======================================================================================================================
# %% calculate weighted mean temperatures for each country
# get coordinates of co-gen plants
db_plants = pd.read_excel(PPLANT_DB)

# setup results df
temp_date_range = pd.date_range(pd.datetime(YEARS[0], 1, 1), pd.datetime(YEARS[-1], 12, 31), freq='D')
daily_mean_temp = pd.DataFrame(index=temp_date_range.values, columns=[cfg.zones])

for zne in cfg.zones:
    chp = db_plants[(db_plants['UnitCoGen'] == 1) & (db_plants['UnitNameplate'] >= 10) &
                    (db_plants['PlantCountry'] == COUNTRY[zne])]
    chp_lon = chp['PlantLongitude'].values
    chp_lat = chp['PlantLatitude'].values

    for year in YEARS:
        filename = os.path.join(ERA_DIR, f'temperature_europe_{year}.nc')
        era5 = Dataset(filename, format='NETCDF4')
        # get grid
        lats = era5.variables['latitude'][:]  # y
        lons = era5.variables['longitude'][:]  # x

        DAYS = range(0, days_in_year(year), 1)
        for day in DAYS:
            hour = day * 24
            temp_2m = era5.variables['t2m'][hour, :, :] - 273.15
            # obtain weighted average temperature from interpolation function, using CHP capacities as weights
            f = interpolate.interp2d(lons, lats, temp_2m)
            temp_itp = np.diagonal(f(chp_lon, chp_lat)) * chp['UnitNameplate'].values / chp['UnitNameplate'].sum()
            era_date = num2date(era5.variables['time'][hour], era5.variables['time'].units,
                                era5.variables['time'].calendar)
            daily_mean_temp.loc[era_date, zne] = np.nansum(temp_itp)

# %% export results
daily_mean_temp.replace(-9999, np.nan, inplace=True)
daily_mean_temp.to_csv(medea_path('data', 'processed', 'temp_daily_mean.csv'))
