# ---------------------------------------------------------------
# %% Settings & Scenario Assumptions
project = 'wind_vs_pv'
fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal', 'Biomass']
# naming of output gdx
output_naming = '{}_eua-{}_won-{}'

# ---------------------------------------------------------------
# Scenario Assumptions
# calibration of power plant efficiencies
efficiency = {
    # [plant efficiencies]
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.15],
    'e_Coal': [1.225],
    'e_Gas': [1.15],
    'e_Oil': [1]
}

# [capacities in 2030]
# - thermal capacities relative to installed capacities in 2016
# - intermittent capacities in GW(p)
x = list(range(15, -1, -1))
x.insert(0, float('inf'))
scenario_2030 = {
    'AT': {
        'bio': [0.8],
        'coal': [0],
        'heatpump': [1],
        'lig': [0],
        'ng': [0.85],
        'nuc': [0.8],
        'oil': [0.85],
        'wind_on': [2.6],
        'wind_off': [0],
        'pv': [1.1],
        'd_power': [1.18276362],
        'lim_wind_on': x
    },
    'DE': {
        'bio': [0.85],
        'coal': [0.35],
        'heatpump': [1],
        'lig': [0.45],
        'ng': [0.9],
        'nuc': [0.0],
        'oil': [0.9],
        'wind_on': [90.8],
        'wind_off': [15],
        'pv': [73]
    }
}

# [CO2 emission prices]
eua_range = range(10, 81, 10)

# [electricity exchange]
electricity_exchange = {
    'Autarky': [0],
    'Openness': [float('inf')]
}
