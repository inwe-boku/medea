# This file holds all scenario-specific settings and assumptions

PROJECT_NAME = 'asparagus'
# -------------------------------------------------------------------------------------------------------------------- #
"""
Description:
determine optimal investment in Austrian dispatchable and intermittent energy generation and storage technologies 
in 2030, given
    a) the targets of the Austrian energy- and climate strategy ("mission 2030"), notably
        a1) 100% of electricity consumption met from domestic, renewable sources (annual average, 
            excluding industry own-consumption, i.e. effectively 90% of consumption)
        a2) balanced international electricity exchange (on annual average)
        a3) reduction of transport sector CO2-emissions by 7.2 mn t, translating in a fuel consumption reduction of 
            27.3 TWh, which, if substituted by battery-electric mobility, raises electricity demand by 12.5 TWh.
    b) restrictions on land availability for wind turbines due to social conflicts
Our analysis allows for electricity exchange with Germany, Austria's most important electricity trading partner and 
accounts for Germany's nuclear exit and its proposed coal phase-out.
As restrictions on land availability for wind turbines are not specified, we generate scenarios of deployable wind 
turbine capacity in the range between 0 and unconstrained deployment. This is repeated for a range of CO2 price 
assumptions.
For sensitivity analysis, we also vary the capitalcost of solar PV. 
"""

# campaigns
dict_campaigns = {
    'base': {
        'co2_price': range(120, 29, -30),
        'wind_cap': range(18, -1, -2),
        'pv_cost': [36715, 16715]
    },
    'cheappv': {
        'co2_price': [30, 60, 120],
        'wind_cap': range(18, 17, -2),
        'pv_cost': range(36715, 16026, -1000)
    }
}

"""
CAPACITY ASSUMPTIONS
- GERMANY:
  - nuclear exit
  - proposal of coal commission is followed, i.e. reduction of 9 GW lignite and 11 GW coal till 2030
  - oil and natural gas-fired capacities remain unchanged
  - biomass additions according to EEG 2017 (+1.05 GW)
- AUSTRIA:
  - follows scenario 2030 DG from ENTSO-E's Ten Year Network Development Plan 2018 (TYNDP 2018) for
    conventional capacities:
             Country    Gas   Hard coal   Oil   Biomass
    2030 DG       AT   3928           0   174       620
  - endogeneous optimization of intermittent capacities from baseline
"""
# electricity consumption in Austria in 2016 excluding distribution losses and own consumption: 62 038,515 GWh
# projected increase in electricity consumption up to 2030: 27 000 GWh

scenario_2030 = {
    'AT': {
        'bio': [5.59],
        'coal': [0],
        'heatpump': [1],
        'lig': [0],
        'ng': [0.86],
        'nuc': [0],
        'oil': [0.29],
        'wind_on': [2.6],
        'wind_off': [0],
        'pv': [1.1],
        'ror': [6.7],
        'd_power': [62038.515 + 17600]
    },
    'DE': {
        'bio': [1.3],
        'coal': [0.56],
        'heatpump': [1.0],
        'lig': [0.56],
        'ng': [1.0],
        'nuc': [0.0],
        'oil': [1.0],
        'wind_on': [90.8],
        'wind_off': [15],
        'pv': [73],
        'ror': [4.5]
    }
}

# calibration of power plant efficiencies
efficiency = {
    # [plant efficiencies] -------------- #
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.0],
    'e_Coal': [1.0],
    'e_Gas': [1.0],
    'e_Oil': [1]
}