
download_entsoe:
		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/get_entsoe.py

#download_era5:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/get_temperatures.py
#
#download_quandl:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/get_pricedata.py
#
#process_heatload: download_era5
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/get_heatload.py
#
#process_commercialflows:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/compile_CommercialFlows.py
#
#process_hydrogeneration:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/compile_HydroGeneration.py
#
#process_reservoirfilling:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/compile_ReservoirFilling.py
#
#data_preprocessing: download_entsoe download_quandl process_heatload process_commercialflows process_hydrogeneration process_reservoirfilling
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%g) python3 -m  src/data/compile_timeseries.py
#
#gdx:
#		FOR /F "tokens=*" %g IN ('chdir') do (SET PYTHONPATH=%PYTHONPATH%;%g) python3 -m  src/tools/instantiate_gdx.py
#
#gdx_update: data_preprocessing gdx
#
