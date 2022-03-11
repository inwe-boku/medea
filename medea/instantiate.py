"""
This script can be executed to download and pre-process data to instantiate the power system model medea with data
for Austria and Germany.
The procedure is explained step-by-step in doc/getting_started.md and requires previous initialization of the
medea-model via
from medea.init import medea_init
ROOT_DIR = 'path/to/your/project/directory'
medea_init(ROOT_DIR)
"""
# %% imports
from pathlib import Path
import yaml
import pandas as pd
import gamstransfer as gt
from medea_data_atde import compile_symbols
from medea_data_atde.retrieve import do_download, init_medea_data_atde
from medea_data_atde.process import do_processing
from config import ROOT_DIR

# %% Settings / Parameters
zones = ['AT', 'DE']
years = range(2012, 2020)  # years for which data is pre-processed
year = 2019  # year for which gdx is created

root_dir = Path(ROOT_DIR)
timeseries = root_dir / 'data' / 'processed' / 'time_series.csv'

credentials = yaml.load(open(ROOT_DIR / 'credentials.yaml'), Loader=yaml.SafeLoader)
USER = credentials['entsoe']['user']
PWD = credentials['entsoe']['pwd']
API_KEY = credentials['quandl']['apikey']
CDSURL = credentials['copernicus']['url']
CDSKEY = credentials['copernicus']['key']

country = {
    'AT': 'Austria',
    'DE': 'Germany',
}

CATEGORIES = [
    'ActualGenerationOutputPerGenerationUnit_16.1.A',
    'AggregatedGenerationPerType_16.1.B_C',
    'AggregatedFillingRateOfWaterReservoirsAndHydroStoragePlants_16.1.D',
    'TotalCommercialSchedules_12.1.F'
]

url_ageb_bal = {
    12: ['2021/01', 'xlsx'],
    13: ['2021/01', 'xlsx'],
    14: ['2021/01', 'xls'],
    15: ['2021/01', 'xlsx'],
    16: ['2021/01', 'xls'],
    17: ['2021/01', 'xlsx'],
    18: ['2020/04', 'xlsx'],
    19: ['2021/11', 'xlsx']
}

url_ageb_sat = {
    12: ['2021/01', 'xlsx'],
    13: ['2021/01', 'xlsx'],
    14: ['2021/01', 'xls'],
    15: ['2021/01', 'xlsx'],
    16: ['2021/01', 'xls'],
    17: ['2021/01', 'xlsx'],
    18: ['2021/01', 'xlsx'],
    19: ['2021/11', 'xlsx']
}

# %% initialize medea-data for Austria and Germany
init_medea_data_atde(root_dir)

# %% download data from external sources
do_download(root_dir, zones, USER, PWD, API_KEY, years, CATEGORIES, url_ageb_bal, url_ageb_sat, CDSURL, CDSKEY)

# %% pre-process data
do_processing(root_dir, country, years, zones, url_ageb_bal)

# %% compile data for subsequent instantiation in a gdx-file
sets, parameters = compile_symbols(root_dir, timeseries, zones, year)

# %% write data to gdx
md = gt.Container()
set_clct = {}
for key, df in sets.items():
    set_clct[key] = gt.Set(md, key, records=df)

pm_clct = {}
for key, lst in parameters.items():
    pm_clct[key] = gt.Parameter(md,  key, lst[0], records=lst[1], description=lst[2])

YEAR = gt.Parameter(md, 'YEAR', [], records=pd.DataFrame([year]), description='year of simulation data')

export_location = root_dir / 'opt' / 'medea_main_data.gdx'
md.write(str(export_location))
