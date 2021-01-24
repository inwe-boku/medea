# This file holds all scenario-specific settings and assumptions

PROJECT_NAME = 'opco'
# -------------------------------------------------------------------------------------------------------------------- #
# baseline settings
dict_base = {
    're_share': range(100, 24, -25),
    'wind_on_cap': range(120, -1, -20),
    'must_run': [1]
}

# campaigns
dict_campaigns = {
    'base': {
    }
}

scenario_2016 = {
    'AT': {
        # scaling factors
        'bio': [1],
        'coal': [1],
        'heatpump': [1],
        'hpa': [1],
        'eboi': [1],
        'lig': [1],
        'ng': [1],
        'nuc': [1],
        'oil': [1],
        # levels
        'wind_on': [2.649],
        'wind_off': [0],
        'pv': [1.096],
        'ror': [5.7]  # 5.7 GW (+1.05 GW vs 2016) ror capacity consistent with generating +5 TWh from hydro power
    },
    'DE': {
        # scaling factors
        'bio': [1.3],
        'coal': [0.56],
        'heatpump': [1.0],
        'hpa': [0],
        'eboi': [1],
        'lig': [0.56],
        'ng': [1.0],
        'nuc': [0.0],
        'oil': [1.0],
        # levels
        'wind_on': [90.8],
        'wind_off': [15],
        'pv': [73],
        'ror': [4.5]
    }
}
