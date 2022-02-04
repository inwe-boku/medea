# %% imports
import yaml
from medea_data_atde import *
from config import ROOT_DIR


# %% settings
zones = ['AT', 'DE']
years = range(2012, 2020)

credentials = yaml.load(open(ROOT_DIR / 'credentials.yml'), Loader=yaml.SafeLoader)
user = credentials['entsoe']['user']
pwd = credentials['entsoe']['pwd']
api_key = credentials['quandl']['api']
cdsurl = credentials['copernicus']['cdsurl']
cdskey = credentials['copernicus']['cdskey']

categories = [
    'ActualGenerationOutputPerGenerationUnit_16.1.A',
    'AggregatedGenerationPerType_16.1.B_C',
    'AggregatedFillingRateOfWaterReservoirsAndHydroStoragePlants_16.1.D',
    'TotalCommercialSchedules_12.1.F',
]

url_ageb_bal = {
    12: ['2021/01', 'xlsx'],
    13: ['2021/01', 'xlsx'],
    14: ['2021/01', 'xls'],
    15: ['2021/01', 'xlsx'],
    16: ['2021/01', 'xls'],
    17: ['2021/01', 'xlsx'],
    18: ['2020/04', 'xlsx'],
    19: ['2021/11', 'xlsx']}

url_ageb_sat = {
    12: ['2021/01', 'xlsx'],
    13: ['2021/01', 'xlsx'],
    14: ['2021/01', 'xls'],
    15: ['2021/01', 'xlsx'],
    16: ['2021/01', 'xls'],
    17: ['2021/01', 'xlsx'],
    18: ['2021/01', 'xlsx'],
    19: ['2021/11', 'xlsx']}

country = {'AT': 'Austria', 'DE': 'Germany'}

# %% set up project

do_download(ROOT_DIR, zones, user, pwd, api_key, years, categories, url_ageb_bal, url_ageb_sat, cdsurl, cdskey)
do_processing(ROOT_DIR, country, years, zones, url_ageb_bal)
