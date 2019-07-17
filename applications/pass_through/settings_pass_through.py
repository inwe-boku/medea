# ---------------------------------------------------------------
# %% Settings & Scenario Assumptions
project = 'pass_through'
fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal', 'Biomass']
techs = ['bio', 'coal', 'lig', 'ng', 'nuc', 'oil', 'wind_on', 'wind_off', 'pv']

capacity_scenario_name = ['cap_avail', 'cap_inst', 'cap_2030']
# naming of output gdx
output_naming = '{}_eua{}'

# ---------------------------------------------------------------
# Scenario Assumptions
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

capacity_scenarios = {
    'AT': {
        'bio': [0.8, 1, 0.8],
        'coal': [0.75, 1, 0],
        'heatpump': [1, 1, 1],
        'lig': [0.8, 1, 0],
        'ng': [0.85, 1, 0.85],
        'nuc': [0, 0, 0],
        'oil': [0.85, 1, 0.85],
        'wind_on': [2, 2, 8],
        'wind_off': [0, 0, 0],
        'pv': [1, 1, 5]
    },
    'DE': {
        'bio': [0.8, 1, 0.85],
        'coal': [0.75, 1, 0.35],
        'heatpump': [1, 1, 1],
        'lig': [0.88, 1, 0.45],
        'ng': [0.9, 1, 0.9],
        'nuc': [0.72, 1, 0],
        'oil': [0.9, 1, 0.9],
        'wind_on': [50, 50, 90.8],
        'wind_off': [5, 5, 15],
        'pv': [50, 50, 73]
    }
}

eua_range = range(5, 76, 5)
