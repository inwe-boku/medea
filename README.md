![MIT License](https://img.shields.io/github/license/inwe-boku/medea.svg)

_medea_
=======

This repository contains code for the power system model _medea_, developed by 
[Sebastian Wehrle](https://sites.google.com/site/sebwehrle/) and 
[Johannes Schmidt](https://homepage.boku.ac.at/jschmidt/).

_medea_ was used to analyze [district heating systems under high CO2 prices](https://arxiv.org/abs/1810.02109)
and is currently employed within the [reFUEL](https://refuel.world) project.

[comment]: #(## Structure ##)
[comment]: # (as of April 1, 2019:)
[comment]: # (* `medea/config.py` holds configuration parameters, such as working directories and model settings)
[comment]: # (* `medea/medea/solve.py` solves the `*.gms`-models in `medea/medea/opt/` according to settings in `medea/config.py`)
[comment]: # (* `medea/medea/scenario_solve.py` is used to calibrate the model and define scenarios (i.e. modify parameters) for for example for the paper "District Heating Systems under high Emission Cost: The Role of the Pass-Through from Emission Cost to Electricity Prices".)
[comment]: # (* `medea/medea/opt/medea_data.gdx` holds exemplary model data) 

Requirements
-------------
* approx. XX GB disk space, at least 16 GB RAM 
* python 3
* for python dependencies: see [requirements.txt](https://github.com/inwe-boku/medea/blob/master/requirements.txt)
* [GAMS](https://www.gams.com/) &ge; 24.8.5
* a solver for mathematical programs, such as [Gurobi](http://www.gurobi.com/)


Installation
------------
* **python**: an easy, yet lightweight way to install python is via [miniconda](https://conda.io/miniconda.html).
python packages dependencies can be installed via 
    ```
    conda install --yes --file requirements.txt
    ``` 
* **GAMS-python bindings**: [download](https://www.gams.com/download/) and install GAMS, then follow these [instructions](https://www.gams.com/latest/docs/API_PY_TUTORIAL.html).


## Setup ##
For _medea_ to work properly, the variables `folder` and `gams_sysdir` in `medea/config.py` must point to the correct locations, i.e. `folder` must point 
to the local medea repository (e.g. `D:\git_repos\medea`) and `gams_sysdir` must point to the
 local GAMS installation (e.g. `C:\GAMS\win64\25.1`)
 
------- 
 For comments and bug reporting please contact [Sebastian Wehrle](mailto:sebastian.wehrle@boku.ac.at).