# This file holds all scenario-specific settings and assumptions
PROJECT_NAME = 'asparagus'

# -------------------------------------------------------------------------------------------------------------------- #
# %% CAMPAIGNS and SCENARIOS

# baseline settings
dict_base = {
    'must_run': [1],
    'policy': [1],
    'co2_price': range(100, -1, -25),
    'wind_cap': range(20, -1, -2),
    'pv_cost': [36424],
    'transmission': [4.9],
}

# campaigns
dict_campaigns = {
    # baseline scenario
    'base': {

    },
    # sensitivity of results to overnight cost of solar PV
    'pv_sens': {
        'wind_cap': [max(dict_base['wind_cap'])],
        'pv_cost': range(36424, 15026, -1500),
    },
    # no (artificial) bottleneck that constrains electricity trade between AT and DE
    'no_bottleneck': {
        'transmission': [10],
    },
    # calculates the opportunity cost of wind turbines at low overnight cost for solar PV
    'low_cost': {
        'pv_cost': [32530],
    },
}

# %% SCENARIO ASSUMPTIONS
"""
CAPACITIES:
- GERMANY:
  - nuclear exit
  - Coal-fired Power Generation Termination Act requires reduction to 9 GW lignite and 8 GW coal by 2030
  - oil and natural gas-fired capacities remain unchanged
  - EEG 2021:
    - Biomass: 8.4 GW
    - Solar PV: 100 GW
    - Wind onshore: 71 GW
    - Wind offshore: 20 GW
- AUSTRIA:
  - follows scenario 2030 DG from ENTSO-E's Ten Year Network Development Plan 2018 (TYNDP 2018) for
    conventional capacities:
             Country    Gas   Hard coal   Oil   Biomass
    2030 DG       AT   3928           0   174       660
  - endogenous optimization of intermittent capacities from baseline

ELECTRICITY DEMAND:
- AUSTRIA:
  - government programme states that 27 TWh electricity need to be added to reach renewable electricity generation equal to
    "100%" of electricity consumption (excluding industry self consumption and system services).
  - Renewable electricity generation in Austria stood at 51 097 712 MW in 2016 and at 54 392 883 MWh in 2019 (Statistic 
    Austria, 2020)
  - Industry own generation and consumption (calculated as total fossil generation from industry-owned units (UEA)) 
    totalled 4 752 907 MWh in 2016 and 4 900 520 MWh in 2019 (Statistics Austria, 2020).
  - Total electricity consumption in 2030 thus is expected to amount to 54 392 883 MWh + 4 900 520 MWh + 27 TWh = 
    86 293 403 MWh (2019) plus system services (82 850 619 MWh plus system services based on 2016 data).
  - Distribution losses (2016: 3 339 001 MWh, 2019: 3 304 538 MWh) and the energy industry's own consumption 
    (2016: 6 953 110 MWh, 2019: 7 158 643 MWh) are included in total consumption, i.e. need not be separately accounted for.
- GERMANY:
  - https://www.bmwi.de/Redaktion/DE/Pressemitteilungen/2021/07/20210713-erste-abschaetzungen-stromverbrauch-2030.html
    electricity consumption in 2030 is expected between 645 and 665 TWh, with a mean of 655 TWh.
    Expected are 14 million electric vehicles, 6 million heatpumps and 30 TWh electricity for hydrogen production
    - Electrolysis capacity of 5 GW envisioned in hydrogen strategy (implies 6000 full load hours)
"""

scenario_2030 = {
    'AT': {
        # scaling factors
        'bio': [1],
        'coal': [0],
        'heatpump': [1],
        'hpa': [1],
        'eboi': [1],
        'lig': [0],
        'ng': [0.86],
        'nuc': [0],
        'oil': [0.5],
        # levels
        'wind_on': [3.164],
        'wind_off': [0],
        'pv': [1.976],
        'ror': [6.84],  # (+1.04 GW vs 5.796 GW in 2020) consistent with generating +5 TWh from hydro power
        'h2': [0.5],
        'd_power': [83193.3]
    },
    'DE': {
        # scaling factors
        'bio': [1.3],
        'coal': [0.3203],
        'heatpump': [1.0],
        'hpa': [0],
        'eboi': [1],
        'lig': [0.4435],
        'ng': [1.0],
        'nuc': [0.0],
        'oil': [1.0],
        # levels for initial capacities (as in 2020)
        'wind_on': [54.420],
        'wind_off': [7.747],
        'pv': [53.848],
        'ror': [4.5],
        'h2': [5],
        'd_power': [655000.0]
    }
}
