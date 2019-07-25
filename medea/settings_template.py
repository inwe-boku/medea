# This file holds all scenario-specific settings and assumptions

# -------------------------------------------------------------------------------------------------------------------- #
#example: CO2 price scenarios

# naming of output gdx
output_naming = 'co2price_{}'

# calibration of power plant efficiencies
efficiency = {
    # [plant efficiencies] -------------- #
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.15],
    'e_Coal': [1.225],
    'e_Gas': [1.15],
    'e_Oil': [1]
}

# range of CO2 prices to be analyzed
range_co2price = range(0, 100, 20)
