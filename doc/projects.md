## Custom applications of _medea_
The functionalities described above allow for rapid development of customized scenario analyses on the basis of 
pre-compiled data. (Data compilation is treated in `./doc/compiling_data.md`.)

To start a new _medea_-project, call the function
```
create_project('project_name', 'medea_dir')
```
contained in `./src/tools/create_project.py`. In the python console this can be done like this:
```python
import config as cfg
from src.tools.create_project import create_project

create_project('new_project', cfg.MEDEA_ROOT_DIR)
```
This creates a standard folder structure for custom projects in `./projects` and copies several templates to these 
folders. 
Details are explained in the following sections after some terminology was introduced.

##### folder structure
Thus, the folder `./projects` holds all medea projects, including two example projects  _`pass_through`_ 
and _`wind_vs_pv`_. 
Every project folder is self-contained (i.e. no additional code or data required from other locations apart from 
functions imported from `./src/tools/gams_io.py`) and contains the following directories:
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
At the top level, the `./projects` directory contains python-scripts to conduct scenario runs related to the 
project. These scripts are:
*   `settings_{project_name}.py`: holds all assumptions used for scenario generation, e.g. data used to calibrate 
power plant efficiencies or a range of CO2 prices to be investigated.
*  `run_{project_name}.py`: iteratively solves the _medea_-model for each scenario and dumps an output .gdx-file to
`./applications/opt`   
*  `results_{project_name}.py`: reads and processes the model output for further use after `run_{project_name}.py` 
has been executed. Results are stored in `./applications/results`.

Upon project creation all files hold example code that should be executable.
However, all scripts should be modified to serve the purpose of the intended analysis.