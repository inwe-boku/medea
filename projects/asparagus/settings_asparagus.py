# This file holds all scenario-specific settings and assumptions

PROJECT_NAME = 'asparagus'

# -------------------------------------------------------------------------------------------------------------------- #
# %% CAMPAIGNS and SCENARIOS

# baseline settings
dict_base = {
    'must_run': [1],
    'policy': [1],
    'co2_price': range(100, -1, -25),
    'wind_cap': range(16, -1, -2),
    'pv_cost': [36424],  # [36424, 32530] with open-space / rooftop as stated by Gewessler
    'transmission': [4.9],
    'd_power': [79302.65]  # *
}
# * government programme states that 27 TWh electricity need to be added to reach renewable electricity generation equal
# to "100%" of electricity consumption (excluding industry self consumption and system services).
# In 2016, renewable electricity generation in Austria was 51.1 TWh. Adding to this the 27 TWh of additional renewable
# generation and industry self generation and consumption (4.75 TWh in 2016 *§) as well as electricity consumption for
# ancillary services (which we do not model) we arrive at total electricity consumption of
# 51.1 TWh + 27 TWh + 4.75 TWh = 82.85 TWh in 2030
# *§ Industry own generation and consumption was calculated as total fossil generation from industry-owned units (UEA)
# (excluding energy industry). In 2016 this equates to 4 752 907 MWh, according to extended energy balances of
# Statistics Austria (2020).

# campaigns  -- total number of runs: 35+75+35+35+5+35=260; 220 * 11 min = ~40 Stunden Rechenzeit
dict_campaigns = {
    # 'base': {  # 5 x 9 = 45 runs
    # },
    'base_hist': {  # 5 x 9 = 45 runs
    },
    # 'uncopt_DE': {  # 5 x 9 = 45 runs
    # },
    ## sensitivity of results to overnight cost of solar PV
    # 'pv_sens': {  # 5 x 15 = 75 runs
    #    'wind_cap': [max(dict_base['wind_cap'])],
    #    'pv_cost': range(36424, 15026, -1500),  # range(25924, 15026, -1500),
    # },
    # sensitivity to PV capital cost with historical capacity factors
    'pv_sens_hist': {  # 5 x 15 = 75 runs
        'wind_cap': [max(dict_base['wind_cap'])],
        'pv_cost': range(36424, 15026, -1500),  # range(25924, 15026, -1500),
    },
    ## no (artificial) bottleneck that constrains electricity trade between AT and DE (which was put in place in 2018 to
    ## prevent loop-flows from DE to AT through eastern Europe
    # 'no_bottleneck': {  # 5 x 9 = 45 runs
    #    'transmission': [10],
    # },
    ## no (artificial) bottleneck that constrains electricity trade between AT and DE (which was put in place in 2018 to
    ## prevent loop-flows from DE to AT through eastern Europe
    'no_bottleneck_hist': {  # 5 x 9 = 45 runs
        'transmission': [10],
    },
    ## disables the must-run condition mimicking ancillary services requirements
    # 'must_run': {  # 5 x 9 = 45 runs
    #    'must_run': [0],
    #	'co2_price': range(75, -1, -25),
    # },
    ## disables the policy objective of generating sufficient electricity from renewable sources under 2030 conditions
    # 'no_policy': {  # 5 runs
    #    'policy': [0],
    #    'co2_price': [25, 42, 45, 50, 63],
    #    'wind_cap': [max(dict_base['wind_cap'])],
    # },
    # calculates the opportunity cost of wind turbines at low overnight cost for solar PV
    # 'low_cost': {  # 5 x 9 = 45 runs
    #    'pv_cost': [32530],  # [22146, 29285],
    # },
    # calculates the opportunity cost of wind turbines at low overnight cost for solar PV
    'low_cost_hist': {  # 5 x 9 = 45 runs
        'pv_cost': [32530],  # [22146, 29285],
    }
    ##     # # disables policy objective and sets generation capacities & electricity demand to 2016 level
    ##     # 'base-2016': {
    ##     #     'policy': [0],
    ##     #     'wind_cap': [max(dict_base['wind_cap'])],
    ##     #     'd_power': [65377.516]  # **
    ## }
}
# ** end-use plus transmission losses as of 2016. excludes energy sector own consumption as plant efficiencies are net

# %% CAPACITY ASSUMPTIONS
"""
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
  - endogenous optimization of intermittent capacities from baseline
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
        'wind_on': [2.649],
        'wind_off': [0],
        'pv': [1.096],
        'ror': [6.75],  # 5.7 GW (+1.05 GW vs 2016) ror capacity consistent with generating +5 TWh from hydro power
        'h2': [0]
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
        # levels
        'wind_on': [54.420],  # [90.8], reset to 2020 capacity account for 4MW wind turbine profile
        'wind_off': [7.747],
        'pv': [53.848],
        'ror': [4.5],
        'h2': [0]
    }
}
