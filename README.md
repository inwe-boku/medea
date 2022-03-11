![MIT License](https://img.shields.io/badge/license-MIT-green)

_medea_
=======

_medea_ is a power system model, developed by [Sebastian Wehrle](https://homepage.boku.ac.at/sebwehrle/index.html) and
[Johannes Schmidt](https://homepage.boku.ac.at/jschmidt/). This repository contains code for the abstract model along
with dummy data. 
Code to download and compile actual data for Austria and Germany is provided in the
[medea-data-atde](https://github.com/boku-inwe/medea-data-atde) repository.

_medea_ is currently employed within the [reFUEL](https://refuel.world) and 
[NetZero2040](https://twitter.com/netzero2040) projects.

Recently, _medea_ was used to assess _The cost of undisturbed landscapes_. The corresponding peer-reviewed publication
can be found [here](https://doi.org/10.1016/j.enpol.2021.112617). The replication code for the model can be
found [here](https://github.com/inwe-boku/medea/releases/tag/v0.2-cost_of_undisturbed_landscapes).

Requirements
-------------
* at least 16 GB RAM, 32 GB recommended 
* python 3.6 or later
* for python dependencies: see [requirements.txt](https://github.com/inwe-boku/medea/blob/master/requirements.txt)
* [GAMS](https://www.gams.com/) 24.8 or later
* a solver for mathematical programs, such as CPLEX or [Gurobi](http://www.gurobi.com/)

Installation of _medea_ and its prerequisites
------------
* **python**: an easy, yet lightweight way to install python is via [miniconda](https://conda.io/miniconda.html).

* **GAMS and GAMS-python API**: [download](https://www.gams.com/download/) and install GAMS, then follow these 
[instructions](https://www.gams.com/latest/docs/API_PY_TUTORIAL.html) to set up the GAMS-python API. (Remember to activate the appropriate python-envorinment beore installing the GAMS-python API)

* **git**: [download](https://git-scm.com/downloads) and install git

## Setting up _medea_ and getting started ##
For more information on how to set up and use _medea_, please consult
[_getting started_](https://github.com/inwe-boku/medea/blob/master/doc/getting_started.md).


------- 
Feel free to use the github-tools for bug reporting, feature requests etc. You can also
[contact me](mailto:sebastian.wehrle@boku.ac.at).

------
We gratefully acknowledge support from the European Research Council (“reFUEL” ERC2017-STG 758149) and the Austrian 
Klimafonds as part of the 13th Austrian Climate Research Programme (“NetZero2040” KR20AC0K18182).