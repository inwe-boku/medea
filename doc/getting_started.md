install GAMS
--- 
download and install GAMS from [https://www.gams.com](https://www.gams.com)

install and set up python 
---
Install python on your machine. For Windows I like the light-weight yet still comfortable [miniconda](https://docs.conda.io/en/latest/miniconda.html).
An IDE is not required, but can make working with python much more comfortable. Personally, I like [pycharm](https://www.jetbrains.com/pycharm/).

Set up a python 3 (conda) environment compatible with GAMS (currently I recommend python 3.9)

install medea and a medea data package
--
The core of _medea_ is an _abstract_ implementation of a power system model, that describes the functioning of the 
system but is independent of any specific parametrization. This model is distributed through the repository 
[https://github.com/inwe-boku/medea](https://github.com/inwe-boku/medea).
The abstract model is fully functioning and allows for extensions and modifications. Further details are described in 
[`./doc/abstract_model.md`](/doc/abstract_model.md).

To solve the abstract model, it needs to be instantiated with data. The repository 
[https://github.com/inwe-boku/medea_data_atde](https://github.com/inwe-boku/medea_data_atde) provides a python package 
that downloads and processes power system data for Austria and Germany and subsequently hands it over to the abstract 
model.

To install both packages via the command line:
```commandline
conda install git pip
pip install git+https://github.com/sebwehrle/medea_data_atde.git
pip install git+https://github.com/sebwehrle/medea.git
```

do medea init
---
Typically, _medea_ is used for a specific application, called "_project_". It is recommended to keep all code and data in an 
application-specific project-repository. Such a repository is expected to follow a given directory structure and can
be initialized through the Python console:

```python
from medea.init import init_medea
ROOT_DIR = 'path/to/your/project/directory'
init_medea(ROOT_DIR)
```

download data
---
The automated data download requires access to these sources:
* [ENTSO-E transparency platform](https://transparency.entsoe.eu/) (go to "Login", then "Register")
* [Copernicus Climate Data Store](https://cds.climate.copernicus.eu) (go to "Login/register")
* [quandl]() (service terminated - looking for an alternative)

Fill the respective credentials into `credentials.yaml`.
````yaml
entsoe:
  user: user_name
  pwd: password

quandl:
  apikey: your_apikey

copernicus:
  url: url://to.copernicus.cds/api
  key: your_cds_key
````
Once _medea_ is initialized and the required log-in data is inserted into `credentials.yaml`, data can be retrieved 
through the Python console. 
Alternatively, all subsequent steps can also be carried out by running `medea/instantiate.py`.

````python
from pathlib import Path
import yaml
from medea_data_atde.retrieve import do_download, init_medea_data_atde
from config import ROOT_DIR

ROOT_DIR = Path(ROOT_DIR)
credentials = yaml.load(open(ROOT_DIR / 'credentials.yaml'), Loader=yaml.SafeLoader)
USER = credentials['entsoe']['user']
PWD = credentials['entsoe']['pwd']
API_KEY = credentials['quandl']['apikey']
CDSURL = credentials['copernicus']['url']
CDSKEY = credentials['copernicus']['key']

zones = ['AT', 'DE']
years = range(2012, 2020)
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

init_medea_data_atde(ROOT_DIR)
do_download(ROOT_DIR, zones, USER, PWD, API_KEY, years, CATEGORIES, url_ageb_bal, url_ageb_sat, CDSURL, CDSKEY)

````

pre-process data
---
After data retrieval, the data needs to be pre-processed via the Python console:
(the dictionary `url_ageb_bal` is required to correct for a mess in the download links provided by 
AG Energiebilanzen)

````python
from pathlib import Path
from medea_data_atde.process import do_processing
from config import ROOT_DIR

root_dir = Path(ROOT_DIR)
country = {
    'AT': 'Austria',
    'DE': 'Germany',
}
years = range(2012, 2020)
zones = ['AT', 'DE']

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

do_processing(root_dir, country, years, zones, url_ageb_bal)
````

Compile GAMS symbols and generate gdx data file
---
`year` selects the year for which historical data is used. Currently tested are 2016 and 2019.
Python console:
````python
from pathlib import Path
import pandas as pd
import gamstransfer as gt
from medea_data_atde import compile_symbols
from config import ROOT_DIR

root_dir = Path(ROOT_DIR)

timeseries = root_dir / 'data' / 'processed' / 'time_series.csv'
zones = ['AT', 'DE']
year = 2019

sets, parameters = compile_symbols(root_dir, timeseries, zones, year)

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
````

Run the model
---
Python console:
```python
from pathlib import Path
from medea.execute import run_medea
from config import ROOT_DIR

root_dir = Path(ROOT_DIR)

gams_dir = Path('d:/GAMS/37')
project_dir = root_dir / 'opt'
model_gms = project_dir / 'medea_main.gms'

run_medea(gams_dir, project_dir, model_gms)
```
