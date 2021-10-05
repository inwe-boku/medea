## Basic functionality
The core of medea is implemented in GAMS and contained in `./src/model/medea_main.gms`. The model is documented in 
[`mathematical_description.pdf`](./mathematical_description.pdf)

The GAMS model expects data input via a gdx-file named `medea_main_data.gdx`, located in the same directory as the 
model file. After data preprocessing, the `.gdx`-input is stored in `./data/gdx`.

_medea_ can be run in its base configuration by copying both files in the same folder and starting a GAMS run from the 
command line like this 
```
gams medea_main.gms
``` 
Optionally, several parameters can be invoked when calling GAMS.
* `--scenario` specifies scenario-specific .gdx-data named `medea_%scenario%_data.gdx` that medea expects to read at 
run time.
* `--project` includes a project-specific .gms-file named `medea_%project%.gms` that extends the functionality of the 
core model.
* `--syngas` allows natural gas-fired plant to use synthetic, emission-free methane as fuel, if set to `yes`. By default, 
this option is disabled. 

A medea call including these options and dumping the results to `output.gdx` might then look like
```
gams medea_main.gms --scenario=scenario --project=project --gdx=output.gdx
```
This run requires the files `medea_project.gms` and `medea_scenario_data.gdx` to be present in the folder where the 
model is executed. Otherwise _medea_ will run in its base version, i.e. without model or data adaptations.

