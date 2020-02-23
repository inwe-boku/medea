# Compiling input data for _medea_
### 1) Getting data access
#### Data sources requiring registration
_medea_ makes use of data from several external sources. Some of them require registration. These are:
* _ENTSO-E's transparency data_: you need to register [here](https://transparency.entsoe.eu/usrm/user/createPublicUser).
Please enter your user name and your password in `credentials.yml` (for details see below).  
* _Quandl_: requires registration [here](https://www.quandl.com/sign-up-modal). Once you have registered, you can log 
in and retrieve your personal API key from your profile page. The API key should be stored in `credentials.yml` (see 
below).
* _ERA-5 reanalysis data_: please register [here](https://cds.climate.copernicus.eu/user/register).

#### credentials.yml
_medea_ expects to find login credentials for __ENTSO-E__ and __Quandl__ in `./credentials.yml` in the _medea_ root directory.
The file should look like this:
````yaml
entsoe:
  user: user_name
  pwd: password

quandl:
  apikey: your_apikey
```` 

#### setting up ERA-5 access


### 2) Downloading and processing data
Once you have registered at all sources, set up `credentials.yml` and the connection to ERA-5, you can start downloading 
and processing the raw input data.
To do so, please execute the following scripts in the given order (top to bottom):
```
get_temperatures.py
get_heatload.py
get_entsoe.py
compile_CommercialFlows.py
compile_HydroGeneration.py
compile_ReservoirFilling.py
get_pricedata.py
compile_timeseries.py
```  
Successful execution will generate the file `medea_regional_timeseries.csv`, which is subsequently used to generate 
data input in `.gdx`-format to instantiate the abstract model.

### 3) Generating `.gdx` input data
After the raw data was downloaded and processed, you can create a `.gdx`.file holding the input data for the model. This
can be achieved by running the script
```
src/tools/instantiate_gdx.py
```
Successful execution will generate `medea_main_data.gdx` in `./data/gdx`.

### Reading and writing gdx data
To generate and read `.gdx` databases, _medea_ includes some wrappers around the python-GAMS api. 
These functions can also be convenient for custopm analysis and  are provided by `./src/tools/gams_io.py`.
* `gdx2df(db_gams, symbol, index_list, column_list)` reads data for the symbol (i.e. set, parameter, variable or equation) 
`symbol` from the gams database `db_gams` and generates a pandas data frame with indices as in `index_list` and columns 
as in `column_list`.
* `df2gdx(db_gams, df, symbol_name, symbol_type, dimension_list, desc='None')` writes a symbol of type `symbol_type` 
named `symbol_name` defined over the sets in `dimension_list` to the GAMS database `db_gams`.
*  `reset_parameter(gams_db, parameter_name, df)` writes the data in `df`, which must be stacked in one column, to the 
parameter named `parameter_name` in the GAMS database `db_gams`.
