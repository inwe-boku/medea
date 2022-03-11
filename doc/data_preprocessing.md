# Compiling input data for _medea_
### 1) Getting data access
#### Data sources requiring registration
_medea_ makes use of data from several external sources. Some of them require registration. These are:
* _ENTSO-E's transparency data_: you need to register [here](https://transparency.entsoe.eu/usrm/user/createPublicUser).
Please enter your user name and your password in `credentials.yml` (for details see below).  
* _Quandl_: requires registration [here](https://www.quandl.com/sign-up-modal). Once you have registered, you can log 
in and retrieve your personal API key from your profile page. The API key should be stored in `credentials.yml` (see 
below).
* _ERA-5 reanalysis data_ from the Copernicus Climate Data Store: please register [here](https://cds.climate.copernicus.eu/user/register).

#### credentials.yaml
_medea_ expects to find login credentials for __ENTSO-E__, __Quandl__ and the __Climate Data Store__ in `./credentials.yaml` in the _medea_ root directory.
The file should look like this:
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
