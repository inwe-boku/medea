# Getting started
_medea_ is divided in three parts:
1) data preprocessing (implmented in python)
2) abstract model (implemented in gams)
3) so-called _projects_, which also include data post-processing

Here, we introduce some basic concepts used in _medea_ and give a brief summary of functionalities.
Each part of _medea_ is covered in more detail 

In the following, we describe how to use _medea_ provided that data is already available. 
Generation of the input data is described in [`./doc/data_preprocessing.md`](/doc/data_preprocessing.md).

#### Data preprocessing
We consider _data preprocessing_ as the process of retrieving, converting, and transforming the 
raw data from several sources into a dataset in Gams data exchange-format _.gdx_.

For more details please see [`./doc/data_preprocessing.md`](/doc/data_preprocessing.md)

#### Abstract model
The core of _medea_ is an _abstract_ implementation of a power system model, that describes the functioning of the 
system but is independent of any specific parametrization. 
The abstract model is fully functioning, but allows for extensions and modifications.

Further details are provided in [`./doc/abstract_model.md`](/doc/abstract_model.md)

#### Projects
_medea_ can be used to carry out specific *projects*. 
A project is understood as a task that involves one specific customization of the medea model (which remains in place for the whole project). An example of such a 
customization could be the implementation of some set of energy policies to be analyzed.

While the model customization is fixed, a project may involve many parameter modifications, such as various prices for 
CO<sub>2</sub> or various electricity demand levels. We refer to one collection of parameter modifications (e.g. CO2 price = 50 
EUR/t and electricity demand is 80 TWh per annum) as *scenario*. Hence, one project can consist of many 
scenarios.

_medea_ comes with some support for setting up, running, and post-processing scenarios.
Please see [`./doc/projects.md`](/doc/projects.md) for more details.
