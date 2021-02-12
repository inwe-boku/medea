![MIT License](https://img.shields.io/badge/license-MIT-green)

_medea_
=======

This repository contains code for the power system model _medea_, developed by 
[Sebastian Wehrle](https://sites.google.com/site/sebwehrle/) and 
[Johannes Schmidt](https://homepage.boku.ac.at/jschmidt/).

_medea_ was used to analyze [district heating systems under high CO2 prices](https://arxiv.org/abs/1810.02109)
and is currently employed within the [reFUEL](https://refuel.world) project.

Recently, _medea_ was used in [project _asparagus_](projects/asparagus), in which we investigate the electricity system
cost of undisturbed Austrian landscapes. We present findings at the
[NOeG annual meeting 2020](https://www.wu.ac.at/economics/ver/noeg-tagung) and the [EGU 2020](https://www.egu2020.eu/).
Corresponding slides are available [here](doc/slides.pdf). A preprint of the paper is available at
[arXiv](https://arxiv.org/abs/2006.08009).
 

Requirements
-------------
* at least 16 GB RAM, 32 GB recommended 
* python 3.6 or later
* for python dependencies: see [requirements.txt](https://github.com/inwe-boku/medea/blob/master/requirements.txt)
* [GAMS](https://www.gams.com/) 24.8 or later
* a solver for mathematical programs, such as [Gurobi](http://www.gurobi.com/)


Installation of _medea_ and its prerequisites
------------
* **python**: an easy, yet lightweight way to install python is via [miniconda](https://conda.io/miniconda.html).
python packages dependencies can be installed via 
    ```
    conda install --yes --file requirements.txt
    ``` 
* **GAMS-python bindings**: [download](https://www.gams.com/download/) and install GAMS, then follow these 
[instructions](https://www.gams.com/latest/docs/API_PY_TUTORIAL.html) to set up the GAMS-python API.

* **git**: [download](https://git-scm.com/downloads) and install git

* **_medea_**: fork this repository (try the fork button in the upper right corner) to your github account. Then, copy 
the forked repository's url and `git clone` _medea_ to your local disk.

## Setting up _medea_ ##
For _medea_ to work properly, the variables `folder` and `gams_sysdir` in `medea/config.py` must point to the correct 
locations, i.e. `folder` must point to the local medea repository (e.g. `D:\git_repos\medea`) and `gams_sysdir` must 
point to the folder of the local GAMS installation that contains the GAMS executable. (On Windows this might be
something like `C:\GAMS\win64\27.1`)

## Getting started ##

For more information on how to use _medea_, please consult
[_getting started_](https://github.com/inwe-boku/medea/blob/master/doc/getting_started.md).

------- 
Feel free to use the github-tools for bug reporting, feature requests etc. You can also
[contact me](mailto:sebastian.wehrle@boku.ac.at).

------
We gratefully acknowledge support from the European Research Council (“reFUEL” ERC2017-STG 758149).