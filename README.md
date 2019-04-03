# _medea_
_medea_ power system models 
written by [Sebastian Wehrle](https://sites.google.com/site/sebwehrle/) and [Johannes Schmidt](https://homepage.boku.ac.at/jschmidt/).

This is the git repository of the power system model _medea_ and its derivatives.

_medea_ is under constant development. For comments and bug reporting please contact [Sebastian Wehrle](mailto:sebastian.wehrle@boku.ac.at).  

## Structure ##
as of August 29, 2018:
* medea/**config.py** holds configuration parameters, such as path and iteration parameters
* medea/execute/**solve.py** solves the *.gms-models in MEDEA/model/gamsdir/ by iterating according to settings in MEDEA/config.py
* medea/pass_through/**pt_estimation.py** is used to calibrate the model and define scenarios (i.e. modify parameters) for the paper "District Heating Systems under high Emission Cost: The Role of the Pass-Through from Emission Cost to Electricity Prices". Subsequently, the linear _medea_ model is solved using solve.py.
* medea/execute/gamsdir/**medea_data.gdx** holds the model data required for 

## Installation ##
_medea_ requires *python &ge; 3.6*. 
An easy, yet lightweight way to install python is via [miniconda](https://conda.io/miniconda.html).
To install required python packages you can do `conda install --yes --file requirements.txt` or `pip install -r requirements.txt`.

In addition, GAMS-python bindings must be installed.
For installation, [download](https://www.gams.com/download/) and install GAMS &ge; 24.8.5 and follow these [instructions](https://www.gams.com/latest/docs/API_PY_TUTORIAL.html).

To allow for maximum freedom of choice, calls to GAMS are low-level implementations, avoiding GAMS-python routines
that require specific GAMS versions or licenses.

## Setup ##
For _medea_ to work properly, the variables `folder` and `gams_sysdir` in **config.py** must point to the correct locations, i.e. `folder` must point 
to the local medea repository (e.g. `D:\git_repos\medea`) and `gams_sysdir` must point to the
 local GAMS installation (e.g. `C:\GAMS\win64\25.1`)