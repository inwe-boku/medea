# Getting started
In the following, we describe how to use _medea_ provided that data is already available. 
Generation of the input data is described in `./doc/data_compilation.md`.

## Basic functionality
The core of medea is implemnted in GAMS and contained in `./medea/medea_main.gms`. 
This GAMS script expects data input via a gdx-file named `medea_main_data.gdx`, which is stored in `./medea/data/input`.
_medea_ can be run in its base configuration by copying both files in the same folder and starting a GAMS run from the 
command line like this 
```
gams medea_main.gms
``` 
Optionally, the parameters `--scenario` and `--project` can be provided when calling GAMS.
* `--scenario` specifies scenario-specific .gdx-data named `medea_%scenario%_data.gdx` that medea expects to read at 
run time.
* `--project` includes a project-specific .gms-file named `medea_%project%.gms` that extends the functionality of the 
core model.

A medea call including these options and dumping the results to `output.gdx` might then look like
```
gams medea_main.gms --scenario=scenario --project=project --gdx=output.gdx
```
This run requires the files `medea_project.gms` and `medea_scenario_data.gdx` to be present in the folder where the 
model is executed. Otherwise _medea_ will run in its base version, i.e. without model or data adaptations.

## Reading and writing gdx data
_medea_ includes some wrappers around the python-GAMS api to read and write .gdx-databases from pandas data frames. 
These functions are provided by `./medea/gams_io.py`.
* `gdx2df(db_gams, symbol, index_list, column_list)` reads data for the symbol (i.e. set, parameter, variable or equation) 
`symbol` from the gams database `db_gams` and generates a pandas data frame with indices as in `index_list` and columns 
as in `column_list`.
* `df2gdx(db_gams, df, symbol_name, symbol_type, dimension_list, desc='None')` writes a symbol of type `symbol_type` 
named `symbol_name` defined over the sets in `dimension_list` to the GAMS database `db_gams`.
*  `reset_parameter(gams_db, parameter_name, df)` writes the data in `df`, which must be stacked in one column, to the 
parameter named `parameter_name` in the GAMS database `db_gams`.

## Custom applications of _medea_
The functionalities described above allow for rapid development of customized scenario analyses on the basis of 
pre-compiled data. (Data compilation is treated in `./doc/compiling_data.md`.)

To start a new _medea_-project, call the function
```
create_project('project_name', 'medea_dir')
```
contained in `./medea/projects.py`. In the python console this can be done like this:
```python
import config as cfg
from medea.projects import create_project

create_project('new_project', cfg.folder)
```
This creates a standard folder structure for custom projects in `./applications` and copies several templates to these 
folders. 
Details are explained in the following sections after some terminology was introduced.

##### Terminology: _projects_ and _scenarios_
_medea_ can be applied to carry out specific ***projects***. A project is understood as a task that involves 
one specific customization of the medea model (which remains in place for the whole project). An example of such a 
customization could be the implementation of some set of energy policies to be analyzed.

While the model customization is fixed, a project may involve many parameter modifications, such as various prices for 
CO2 or various electricity demand levels. We refer to one collection of parameter modifications (e.g. CO2 price = 50 
EUR/t and electricity demand is 80 TWh per annum) as ***scenario***. In consequence, one project can consist of many 
scenarios. 

##### folder structure
Thus, the folder `./applications` holds all medea projects, including two example projects  _`pass_through`_ 
and _`wind_vs_pv`_. 
Every project folder is self-contained (i.e. no additional code or data required from other locations apart from 
functions imported from `./medea/gams_io.py`) and contains the following directories:
*   **`doc`** : holds the source code of corresponding publications (if any)
    * **`doc/figures`** : holds publication figures
* **`opt`** : GAMS project folder containing all GAMS model codes as well as input and output .gdx-data files
* **`results`** : collects all post-processed results (generated from output .gdx-files), typically in .csv-format

### Conducting own analysis
##### project-specific modifications of _medea_
Any modifications of the GAMS model should be done through the file 
`./applications/{project_name}/medea_{project_name}.gms`. This file is fed to the main GAMS model file via a `$include`
statement right before the model is solved, i.e. any parameter of the main medea model can be changed and any additional 
constraint can be introduced.
However, `medea_{project_name}.gms` must be self-contained, i.e. any new parameter or equation used in the custom 
model extension must also be defined in the custom model extension. Moreover, scenario data must be loaded from 
.gdx-scenario data files in the custom model extension `medea_{project_name}.gms`. For example:
```
parameter x; 
$gdxin medea_%scenario%_data
$load  x
$gdxin

equation additional_constraint;
additional_constraint.. y =L= x;
```
where `%scenario%` equals the value of a command line option passed to gams upon execution, like
```
gams medea_main.gms --scenario=scenario_name
```

##### setting up scenario analysis with python scripts
At the top level, the `./applications` directory contains python-scripts to conduct scenario runs related to the 
project. These scripts are:
*   `settings_{project_name}.py`: holds all assumptions used for scenario generation, e.g. data used to calibrate 
power plant efficiencies or a range of CO2 prices to be investigated.
*  `run_{project_name}.py`: iteratively solves the _medea_-model for each scenario and dumps an output .gdx-file to
`./applications/opt`   
*  `results_{project_name}.py`: reads and processes the model output for further use after `run_{project_name}.py` 
has been executed. Results are stored in `./applications/results`.

Upon project creation all files hold example code that should be executable.
However, all scripts should be modified to serve the purpose of the intended analysis.  
