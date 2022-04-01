$title medea

*#* TO-DOs:
** THINGS TO ADD:
* - investment in storage capacity
* - derived post-solution variables
* - switches for different model options (short-run/long-run, ancillary services, ...) **** better to implement in python
* - spatially resolved investment in plants / nodes or cells
* - enable fuel trade in supply-demand balance
* - activate transmission technologies

* ==============================================================================
* COMMAND LINE OPTIONS
* ------------------------------------------------------------------------------
* command-line option --PROJECT
* includes .gms-file medea_%PROJECT%.gms right before model-statement, allowing
* for custom modifications to medea
* '--PROJECT=test' is not admissible as it is reserved for unit testing
* ------------------------------------------------------------------------------
* command-line option --SCENARIO
* tries to read data from .gdx-file 'MEDEA_%scenario%_data.gdx'
* if this does not exit, fall back to default 'medea_main_data.gdx'
* ------------------------------------------------------------------------------
* command-line option --NORAGUROBI
* NORAGUROBI no: use default solver on local machine (recommended)
* NORAGUROBI yes: use gurobi solver on nora (only in boku lan)
* ------------------------------------------------------------------------------
* command-line option --SYNGAS
* SYNGAS no: use default fuels for power generation
* SYNGAS yes: allow for use of synthetic gas in natural gas-fired units
* ==============================================================================
$if not set NORAGUROBI $set NORAGUROBI no
$if not set SYNGAS $set SYNGAS no
* ==============================================================================

* enable end.of.line-comments with '#'
$onEoLCom
$EoLCom #

* ==============================================================================
* SYMBOL DECLARATIONS
* ------------------------------------------------------------------------------
Sets
         e                          all energy carriers        - prev "a"
         i(e)                       energy inputs              - prev "f"
         f(e)                       final energy               - prev "m"
         t                          technologies (units)
         c(t)                       co-generation units        - prev "j(i)"
         d(t)                       dispatchable technologies  - prev "i"
         r(t)                       intermittent technologies  - prev "n"
         s(t)                       storage technologies       - prev "k"
         g(t)                       transmission technologies / e_grid, ht_grid, h2_grid /
         l                          limits of feasible operating regions of CHPs
         h                          time \ hours               - prev "t"
         z                          market zones
;
alias(z,zz);
* ------------------------------------------------------------------------------
Parameters
         AIR_POL_COST_FIX(i)        fixed air pollution cost [EUR per MW]
         AIR_POL_COST_VAR(i)        variable air pollution cost [EUR per MWh]
         ANNUITY_FACTOR(z,t)        annuity factor for investment cost
         ANNUITY_FACTOR_X(z,f)      annuity factor for grid investment cost
         CAPACITY(z,t)              installed capacity of conversion units [GW]
         CAPACITY_X(z,zz,f)         initial transmission capacity [GW]
         CAPACITY_STORAGE(z,f,s)    volume of storage [GWh]
         CAPACITY_STORE_IN(z,f,s)   capacity to store in [GW]
         CAPACITY_STORE_OUT(z,f,s)  capacity to store out [GW]
         CAPITALCOST(z,t)           specific annualized overnight cost of construction [EUR per MW]
         CAPITALCOST_E(z,s)         specific capital cost of storage volume [EUR per MWh]
         CAPITALCOST_P(z,s)         specific capital cost of storage capacity [EUR per MW]
         CAPITALCOST_X(z,f)         specific annualized overnight cost of transmission capacity [EUR per MW]
         CO2_INTENSITY(i)           CO2 intensitiy of fuels burned [t CO2 per MWh_th]
         CONVERSION(e,f,t)          conversion efficiency of technologies
         COST_OM_QFIX(t)            quasi-fixed operation and maintenance cost [EUR per MW]
         COST_OM_VAR(t)             variable operation and maintenance cost [EUR per MWh]
         DEMAND(z,h,f)              demand for product f at time h [GW]
         DISCOUNT_RATE(z)           discount rate
         DISTANCE(z,zz)             distance between centers of gravity of market areas [km]
         FEASIBLE_INPUT(l,i,c)      relative fuel requirement at corners of feasible operating region
         FEASIBLE_OUTPUT(l,f,c)     relative energy production at corners of feasible operating region
         INFLOWS(z,h,s)             energy content of (exogenous) inflows to storages [GW]
         LAMBDA                     load scaling factor for system service requirement
         LIFETIME(t)                technical lifetime of unit [a]
         MAP_INPUTS(e,t)            mapping of inputs to technologies
         MAP_OUTPUTS(f,t)           mapping of outputs to technologies
         OVERNIGHTCOST(t)           overnight investment cost of technologies [EUR per kW]
         OVERNIGHTCOST_E(s)         overnight investment cost of storage volume [EUR per kWh]
         OVERNIGHTCOST_P(s)         overnight investment cost of storage technologies [EUR per kW]
         OVERNIGHTCOST_X(f)         overnight investment cost of transmission expansion
         PEAK_LOAD(z)               maximum electricity load [GW]
         PEAK_PROFILE(z,i)          maximum share of generation from intermittent sources [%]
         PRICE_CO2(z,h)             price of CO2 emissions [EUR per t CO2]
         PRICE(z,h,i)               price of energy carrier [EUR per MWh]
         PRICE_TRADE(f)             price of imported energy carriers [EUR per MWh]
         PROFILE(z,h,i)             intermittent generation profile
         SIGMA(z)                   intermittent generation scaling factor for system service requirement
         VALUE_NSE(z)               value of non-served energy [EUR]
         SWITCH_INVEST              switches between long-term and short-term perspective
;

* ------------------------------------------------------------------------------
* load data
$if %PROJECT% == test $gdxin medea_testing_period
$if %PROJECT% == test $load h
$if %PROJECT% == test $gdxin

$if NOT exist MEDEA_%scenario%_data.gdx  $gdxin medea_main_data
$if     exist MEDEA_%scenario%_data.gdx  $gdxin medea_%scenario%_data
$if NOT %PROJECT% == test $load h
$load    e i f t c d r s l z
$load    AIR_POL_COST_FIX AIR_POL_COST_VAR CAPACITY CAPACITY_X CAPACITY_STORAGE
$load    CAPACITY_STORE_IN CAPACITY_STORE_OUT OVERNIGHTCOST OVERNIGHTCOST_E
$load    OVERNIGHTCOST_P OVERNIGHTCOST_X CONVERSION CO2_INTENSITY COST_OM_QFIX
$load    COST_OM_VAR DEMAND DISCOUNT_RATE DISTANCE FEASIBLE_INPUT FEASIBLE_OUTPUT
$load    INFLOWS LAMBDA LIFETIME MAP_INPUTS MAP_OUTPUTS PEAK_LOAD PEAK_PROFILE
$load    PRICE PRICE_CO2 PRICE_TRADE PROFILE SIGMA SWITCH_INVEST VALUE_NSE
$gdxin

* ------------------------------------------------------------------------------
* enable the use of synthetic gas in natural gas-fired plant
$if %SYNGAS% == yes MAP_FUEL_G(i,'Syngas')$MAP_FUEL_G(i,'Gas') = yes;
$if %SYNGAS% == yes EFFICIENCY_G(i, 'el', 'Syngas') = EFFICIENCY_G(i, 'el', 'Gas');
$if %SYNGAS% == yes FEASIBLE_INPUT(i,l,'Syngas') = FEASIBLE_INPUT(i,l,'Gas');

* ------------------------------------------------------------------------------
* derived parameters
ANNUITY_FACTOR(z,t) = (DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(t)) / ((1+DISCOUNT_RATE(z))**LIFETIME(t)-1);
ANNUITY_FACTOR_X(z,f) = (DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME('transmission')) / ((1+DISCOUNT_RATE(z))**LIFETIME('transmission')-1);
CAPITALCOST(z,t) = OVERNIGHTCOST(t) * ANNUITY_FACTOR(z,t);
CAPITALCOST_E(z,s) = OVERNIGHTCOST_E(s) * ANNUITY_FACTOR(z,s);
CAPITALCOST_P(z,s) = OVERNIGHTCOST_P(s) * ANNUITY_FACTOR(z,s);
CAPITALCOST_X(z,f) = OVERNIGHTCOST_X(f) * ANNUITY_FACTOR_X(z,f);

* ------------------------------------------------------------------------------
Variables
         cost_system                total system cost [kEUR]
         cost_zonal(z)              zonal system cost [kEUR]
         x(z,zz,h,f)                (net) commercial exchange between market zones [GW]  # exports are positive - imports negative
;

Positive Variables
        add_x(z,zz,f)               transmission capacity added
        cost_air_pol(z,i)           cost of air pollution
        cost_inputs(z,i,t)          cost of inputs
        cost_emissions(z,i)         cost of CO2 emissions
        cost_om(z,t)                cost of operation and maintenance
        cost_invest(z,t)            cost of investment
        cost_grid(z,f)              cost of grid expansion
        cost_nse(z,f)               cost of non-served demand
        cost_trade(z,f)             cost of trade in energy carriers
        curtail(z,h,f)              discarded energy output
        decommission(z,t)           capacity decommissioned
        emission_co2(z,h,i)         quantity of CO2 emitted
        fuel_trade(z,h,f)           fuel shipment
        gen(z,h,f,t)                energy generation
        invest(z,t)                 capacity investmed
        nse(z,h,f)                  non-served energy
        storage_content(z,h,f,s)    storage capacity
        use(z,h,e,t)                energy use (endogenous)
        w(z,h,c,l,i)                co-generation weight
;
* ==============================================================================

* ==============================================================================
* EQUATION DECLARATION
* equation naming:
* bal: balance - equality constraint, decision variables on both sides
* acn: accounting - equality constraint, decision variable on one side, bookkeeping variable on other
* uplim: upper limit - inequality constraint (less than)
* lolim: lower limit - inequality constraint (greater than)
* ------------------------------------------------------------------------------
Equations
objective, acc_zonal, acc_inputs, acc_emissions, acc_opmaint, acc_invest, acc_grid, acc_nse, acc_trade,
balance, intermittent_generation, energy_conversion, capacity_constraint,
storage_balance,storage_limit,store_in_limit,store_out_limit,
bal_w_chp,uplim_g_chp,lolim_b_chp,
uplim_transmission,lolim_transmission,bal_transmission,bal_add_x,
bal_co2, acn_airpollute,limit_curtail,ancillary_services
;
* ==============================================================================


* ==============================================================================
* MODEL FORMULATION
* ------------------------------------------------------------------------------
* CONSTRAIN VARIABLES
gen.UP(z,h,f,t)$(not MAP_OUTPUTS(f,t)) = 0;
use.UP(z,h,i,t)$(not MAP_INPUTS(i,t)) = 0;
w.UP(z,h,c,l,i)$(NOT MAP_INPUTS(i,c)) = 0;
w.UP(z,h,c,l,i)$(NOT FEASIBLE_INPUT(l,i,c)) = 0;
storage_content.UP(z,h,f,s)$(NOT MAP_OUTPUTS(f,s)) = 0;
storage_content.UP(z,h,f,s)$(NOT MAP_INPUTS(f,s)) = 0;
x.FX(z,zz,h,f)$SAMEAS(z,zz) = 0;
x.FX(zz,z,h,f)$SAMEAS(z,zz) = 0;
x.FX(zz,z,h,'ht') = 0;
emission_co2.UP(z,h,i)$(NOT CO2_INTENSITY(i)) = 0;
curtail.UP(z,h,f)$(NOT MAP_OUTPUTS(f,r)) = 0;
fuel_trade.UP(z,h,f)$(NOT PRICE_TRADE(f)) = 0;
decommission.UP(z,t) = CAPACITY(z,t);
invest.UP(z,t) =  SWITCH_INVEST;

* add_x.UP(z,zz,f)

* ------------------------------------------------------------------------------
* TOTAL SYSTEM COST AND ITS COMPONENTS
objective..
         cost_system
         =E=
         sum(z, cost_zonal(z))
         ;
acc_zonal(z)..
         cost_zonal(z)
         =E=
         sum((i,t), cost_inputs(z,i,t) )
         + sum(i, cost_emissions(z,i) )
         + sum(i, cost_air_pol(z,i) )
         + sum(t, cost_om(z,t) )
         + sum(t, cost_invest(z,t) )
         + sum(f, cost_grid(z,f) )
         + sum(f, cost_nse(z,f) )
         + sum(f, cost_trade(z,f) )
;
acc_inputs(z,i,t)$MAP_INPUTS(i,t)..
         cost_inputs(z,i,t)
         =E=
         sum(h$MAP_INPUTS(i,t), PRICE(z,h,i) * use(z,h,i,t))
         ;
acc_emissions(z,i)$CO2_INTENSITY(i)..
         cost_emissions(z,i)
         =E=
         sum(h, PRICE_CO2(z,h) * emission_co2(z,h,i) )
         ;
acn_airpollute(z,i)..
         cost_air_pol(z,i)
         =E=
         sum(t, AIR_POL_COST_FIX(i) * (CAPACITY(z,t) + invest(z,t) - decommission(z,t)) * MAP_INPUTS(i,t) )
         + sum((h,t), AIR_POL_COST_VAR(i) * use(z,h,i,t) )
         ;
acc_opmaint(z,t)..
         cost_om(z,t)
         =E=
         COST_OM_QFIX(t) * (CAPACITY(z,t) + invest(z,t) - decommission(z,t))
         + sum((h,f), COST_OM_VAR(t) * gen(z,h,f,t)$MAP_OUTPUTS(f,t) )
         ;
acc_invest(z,t)..
         cost_invest(z,t)
         =E=
         CAPITALCOST(z,t) * invest(z,t)
         ;
acc_grid(z,f)..
         cost_grid(z,f)
         =E=
         sum(zz, CAPITALCOST_X(z,f) * add_x(z,zz,f) )
         ;
acc_nse(z,f)..
         cost_nse(z,f)
         =E=
         sum(h, VALUE_NSE(z) * nse(z,h,f) )
         ;
acc_trade(z,f)..
         cost_trade(z,f)
         =E=
         sum(h, PRICE_TRADE(f) * fuel_trade(z,h,f) )
;

* ------------------------------------------------------------------------------
* MARKET CLEARING
balance(z,h,f)..
         DEMAND(z,h,f)
         + sum(zz, x(z,zz,h,f) )
         - nse(z,h,f)
         =E=
         sum(t$MAP_OUTPUTS(f,t), gen(z,h,f,t))
*         + fuel_trade(z,h,'Syngas')
         - sum(t$MAP_INPUTS(f,t), use(z,h,f,t))
         - curtail(z,h,f)
;
* ------------------------------------------------------------------------------
* ENERGY CONVERSION
* Capacity Constraint on Energy Output
* * * * does investment raise capacity for all products? * * * *
capacity_constraint(z,h,f,t)$MAP_OUTPUTS(f,t)..
         gen(z,h,f,t)
         =L=
         CAPACITY(z,t) + invest(z,t) - decommission(z,t)
;
* Intermittent Energy Supply
intermittent_generation(z,h,i,r)..
         use(z,h,i,r)$MAP_INPUTS(i,r)
         =E=
         PROFILE(z,h,i)$MAP_INPUTS(i,r) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r))
;
* Energy Conversion With Fixed Efficiency
energy_conversion(z,h,f,t)$(MAP_OUTPUTS(f,t) AND NOT c(t) AND NOT s(t))..
         gen(z,h,f,t)
         =E=
         sum(i, CONVERSION(i,f,t) * use(z,h,i,t))
;
* Energy Conversion for Flexible Co-Generation Of Heat And Power
bal_w_chp(z,h,c)..
         sum((l,i)$(MAP_INPUTS(i,c) ), w(z,h,c,l,i))
         =L=
         CAPACITY(z,c) + invest(z,c) - decommission(z,c)
;
uplim_g_chp(z,h,c,f,i)$(MAP_INPUTS(i,c) AND MAP_OUTPUTS(f,c))..
         gen(z,h,f,c)
         =E=
         sum(l$(MAP_INPUTS(i,c) ), FEASIBLE_OUTPUT(l,f,c) * w(z,h,c,l,i))
;
lolim_b_chp(z,h,c,i)$MAP_INPUTS(i,c)..
         use(z,h,i,c)
         =E=
         sum(l$(MAP_INPUTS(i,c) ), FEASIBLE_INPUT(l,i,c) * w(z,h,c,l,i))
;
* ------------------------------------------------------------------------------
* CURTAILMENT OF ENERGY
* might be superfluous
limit_curtail(z,h,'el')..
         curtail(z,h,'el')
         =L=
         sum(r, gen(z,h,'el',r) )
;
* ------------------------------------------------------------------------------
* ENERGY STORAGE
storage_balance(z,h,f,s)$MAP_INPUTS(f,s)..
         storage_content(z,h,f,s)
         =E=
         INFLOWS(z,h,s)
         + CONVERSION(f,f,s) * use(z,h,f,s)
         - (1/CONVERSION(f,f,s)) * gen(z,h,f,s)
         + storage_content(z,h-1,f,s)
;
storage_limit(z,h,f,s)$MAP_INPUTS(f,s)..
         storage_content(z,h,f,s)
         =L=
         CAPACITY_STORAGE(z,f,s)
;
store_in_limit(z,h,f,s)$MAP_INPUTS(f,s)..
         use(z,h,f,s)
         =L=
         CAPACITY_STORE_IN(z,f,s) + invest(z,s) - decommission(z,s)
;
store_out_limit(z,h,f,s)$MAP_INPUTS(f,s)..
         gen(z,h,f,s)
         =L=
         CAPACITY_STORE_OUT(z,f,s) + invest(z,s) - decommission(z,s)
;
* ------------------------------------------------------------------------------
* CO2 ACCOUNTING
bal_co2(z,h,i)$CO2_INTENSITY(i)..
         emission_co2(z,h,i)
         =E=
         sum(t, CO2_INTENSITY(i) * use(z,h,i,t))
;
* ------------------------------------------------------------------------------
* EXCHANGE OF ENERGY OUTPUTS BETWEEN MARKET ZONES
uplim_transmission(z,zz,h,f)$(NOT SAMEAS(z,zz))..
         x(z,zz,h,f)
         =L=
         CAPACITY_X(z,zz,f) + add_x(z,zz,f)
;
lolim_transmission(z,zz,h,f)$(NOT SAMEAS(z,zz))..
         x(z,zz,h,f)
         =G=
         - (CAPACITY_X(z,zz,f) + add_x(z,zz,f))
;
bal_transmission(z,zz,h,f)$(NOT SAMEAS(z,zz))..
         x(z,zz,h,f)
         =E=
         - x(zz,z,h,f)
;
bal_add_x(z,zz,f)$(NOT SAMEAS(z,zz))..
         add_x(z,zz,f)
         =E=
         add_x(zz,z,f)
;

* ------------------------------------------------------------------------------
* ANCILLARY SERVICES
ancillary_services(z,h)..
         sum(t$(NOT r(t)), gen(z,h,'el',t) )
*         + gen(z,h,'electricity','ror')
         + sum(t, use(z,h,'el',t))
         =G=
         LAMBDA(z) * PEAK_LOAD(z)
         + SIGMA * sum(r$(NOT SAMEAS(r,'ror')), sum(i,PEAK_PROFILE(z,i) * MAP_INPUTS(i,r)) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r)) )
;

* ==============================================================================


* ==============================================================================
* project control
* ------------------------------------------------------------------------------
$if set PROJECT $include medea_%PROJECT%.gms
* ==============================================================================

model medea / all /;

options
reslim = 54000,
threads = 8,
optCR = 0.01,
BRatio = 1
;

* ==============================================================================
* solve-settings control
* ------------------------------------------------------------------------------
$if %NORAGUROBI% == yes $include solve_with_noragurobi.gms
* ==============================================================================
$onecho > cplex.opt
lpmethod 4
names no
$offecho
medea.OptFile = 1;

solve medea using LP minimizing cost_system;


* ==============================================================================
* REPORTING

* ------------------------------------------------------------------------------
* solve details
scalars modelStat, solveStat;
modelStat = medea.modelstat;
solveStat = medea.solvestat;

* ------------------------------------------------------------------------------
* POST-SOLUTION PARAMETERS
$ontext
PARAMETERS
         Cost_CO2(z,i)           co2 cost
         Cost_Fuel(z,i,t)        fuel cost
         Cost_Interconnect(z,f)  interconnector transmission cost
         Cost_Invest(z,t)        investment cost
         Cost_OnM(z,t)           operation and maintenance cost
         Cost_Zonal(z)           zonal system cost
;

Cost_CO2(z,i) = sum(h, PRICE_CO2(z,h) * emission_co2.L(z,h,i) );
Cost_Fuel(z,i,t) = sum(h$MAP_INPUTS(i,t), PRICE(z,i) * use.L(z,h,i,t));
Cost_Interconnect(z,f) = sum(zz, CAPITALCOST_X(z,f) * add_x.L(z,zz,f) );
Cost_Invest(z,t) = CAPITALCOST(z,t) * invest.L(z,t);
Cost_OnM(z,t) = COST_OM_QFIX(z,t) * (CAPACITY(z,t) + invest.L(z,t)) + sum((h,f), COST_OM_VAR(z,t) * gen.L(z,h,f,t) );
Cost_Zonal(z) = sum((i,t,f),COST_FUEL(z,i,t) + COST_CO2(z,i) + COST_ONM(z,t) + COST_INVEST(z,t) + COST_INTERCONNECT(z,f) );

display Cost_CO2,Cost_Fuel,Cost_Interconnect,Cost_Invest,Cost_OnM,Cost_Zonal;
$offtext
parameters
AnnRenShare(z)                   renewables generation divided by electricity consumption
AnnG(z,f)                        annual thermal generation
AnnGByTec(z,i,t,f)               annual thermal generation by technology
AnnGFossil(z)                    annual generation from fossil sources
AnnGSyngas(z)                    annual generation from synthetic gases
AnnGBiomass(z)                   annual generation from biomass
AnnR(z)                          annual generation from renewable sources
AnnSIn(z)                        annual consumption of electricity storages
AnnSOut(z)                       annual generation of electricity storages
AnnCons(z,f)                     annual consumption of electricity and heat
AnnFullLoadHours(z,r)            annual full load hours of renewable technologies
AnnX(z)                          annual electricity exports
AnnB(z,i)                        annual fuel burn
AnnCO2Emissions(z)               annual CO2 emissions
AnnCurtail(z)                    annual curtailment of generation from renewables
AnnValueG(z,f)                   annual value of thermal generation
AnnValueGByTec(z,t,f)            annual value of thermal generation by technology
AnnValueSIn(z)                   annual value of electricity consumed by storages
AnnValueSOut(z)                  annual value of electricity generated by storages
AnnValueX(z,zz)                  annual value of electricity exports
AnnValueCurtail(z)               annual value of electricity curtailed
AnnCostG(z,t)                    annual cost of thermal generators
AnnRevenueG(z,t)                 annual revenue of thermal generators
AnnProfitG(z,t)                  annual profit of thermal generators
AnnProfitS(z,s)                  annual profit of storages
AnnProfitR(z,r)                  annual profit of renewable generators
AnnSurplusG(z,t)                 annual surplus of thermal generators
AnnProdSurplus(z)                annual producer surplus
AnnSpendingEl(z)                 annual consumer spending on electricity
AnnSpendingHt(z)                 annual consumer spending on heat
AnnSpending(z)                   annual consumer spending on electricity and heat
AvgPriceFuels(z,i)               annual average price of fuels
AvgPriceCO2(z)                   annual average price of CO2 emissions
AvgPriceEl(z)                    annual average price of electricity
AvgPriceHt(z)                    annual average price of heat
HourlyPriceEl(z,h)               hourly price of electricity
HourlyPriceHt(z,h)               hourly price of heat
HourlyPriceSystemServices(z,h)   hourly price of system services
;
* ------------------------------------------------------------------------------
* parameter calculation
*AnnRenShare(z) = (sum((t,n), r.L(z,t,n) ) + sum((t,k), s_out.L(z,t,k) ) - sum((t,k), s_in.L(z,t,k) ) + sum((t,i), g.L(z,t,i,'el','Biomass') ) + sum((t,i), g.L(z,t,i,'el','Syngas') ) ) / sum(t, DEMAND(z,t,'el') );
*AnnG(z,f) = sum((t,i,f), g.L(z, t, i, f, f));
*AnnGByTec(z,i,f,f) = sum(t, g.L(z, t, i, f, f));
*AnnGSyngas(z) = sum((t,i), g.L(z,t,i,'el','Syngas') );
*AnnGBiomass(z) = sum((t,i), g.L(z,t,i,'el','Biomass') );
*AnnGFossil(z) = sum(f, AnnG(z,f)) - AnnGSyngas(z) - AnnGBiomass(z);
*AnnR(z) = sum((t,n), r.L(z,t,n) );
*AnnSIn(z) = sum((t,k), s_in.L(z,t,k));
*AnnSOut(z) = sum((t,k), s_out.L(z,t,k));
*AnnCons(z,f) = sum(t, DEMAND(z,t,f));
*AnnFullLoadHours(z,n) = sum(t, GEN_PROFILE(z,t,n));
*AnnX(zz) = sum(t, x.L('AT',zz,t));
*AnnB(z,f) = sum((t,i), b.L(z,t,i,f));
*AnnCO2Emissions(z) = sum((t,i), emission_co2.L(z,t,i));
*AnnCurtail(z) = sum(t, q_curtail.L(z,t));
*AnnValueG(z,f) = sum((t,i,f), bal_el.M(z,t) * g.L(z,t,i,f,f));
*AnnValueGByTec(z,i,f) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,f,f));
*AnnValueSIn(z) = sum((t,k), bal_el.M(z,t) * s_in.L(z,t,k));
*AnnValueSOut(z) = sum((t,k), bal_el.M(z,t) * s_out.L(z,t,k));
*AnnValueX(z,zz) = sum(t, bal_el.M(z,t) * x.L(z,zz,t));
*AnnValueCurtail(z) = sum(t, bal_el.M(z,t) * q_curtail.L(z,t));
*AnnCostG(z,i) = sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) + cost_om_g.L(z,i);
*AnnRevenueG(z,i) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,'el',f) + bal_ht.M(z,t) * g.L(z,t,i,'ht',f) );
*AnnProfitG(z,i) = AnnRevenueG(z,i) - AnnCostG(z,i);
*AnnProfitS(z,k) = sum(t, bal_el.M(z,t) * s_out.L(z,t,k) - bal_el.M(z,t) * s_in.L(z,t,k) );
*AnnProfitR(z,n) = sum(t, bal_el.M(z,t) * r.L(z,t,n) ) - cost_om_r.L(z,n);
*AnnSurplusG(z,i) = AnnRevenueG(z,i) - sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) - sum((t,f,f), OM_COST_G_VAR(i) * g.L(z,t,i,f,f) );
*AnnProdSurplus(z) = sum(i, AnnSurplusG(z,i)) + sum(k, AnnProfitS(z,k)) + sum((t,n), bal_el.M(z,t) * r.L(z,t,n)) - sum((t,n), OM_COST_R_VAR(z,n) * r.L(z,t,n) );
*AnnSpendingEl(z) =  sum(t, bal_el.M(z,t) * DEMAND(z,t,'el') );
*AnnSpendingHt(z) =  sum(t, bal_ht.M(z,t) * DEMAND(z,t,'ht') );
*AnnSpending(z) =  AnnSpendingEl(z) + AnnSpendingHt(z);
*AvgPriceFuels(z,f) = sum(t, PRICE_FUEL(z,t,f)) / card(t);
*AvgPriceCO2(z) = sum(t, PRICE_CO2(z,t)) / card(t);
*AvgPriceEl(z) = sum(t, bal_el.M(z,t))/card(t);
*AvgPriceHt(z) = sum(t, bal_ht.M(z,t))/card(t);
*HourlyPriceEl(z,t) = bal_el.M(z,t);
*HourlyPriceHt(z,t) = bal_ht.M(z,t);
*HourlyPriceSystemServices(z,t) = lolim_ancservices.M(z,t);

* ==============================================================================
* THE END
* ==============================================================================
* this line intentionally left blank


$ontext
* ------------------------------------------------------------------------------
* EX-POST ANALYSIS
* parameters summarizing model solution - CamelCaseStyle beginning with Ann
parameters
AnnRenShare(z)                   renewables generation divided by electricity consumption
AnnG(z,m)                        annual thermal generation
AnnGByTec(z,i,m,f)               annual thermal generation by technology
AnnGFossil(z)                    annual generation from fossil sources
AnnGSyngas(z)                    annual generation from synthetic gases
AnnGBiomass(z)                   annual generation from biomass
AnnR(z)                          annual generation from renewable sources
AnnSIn(z)                        annual consumption of electricity storages
AnnSOut(z)                       annual generation of electricity storages
AnnCons(z,m)                     annual consumption of electricity and heat
AnnFullLoadHours(z,n)            annual full load hours of renewable technologies
AnnX(z)                          annual electricity exports
AnnB(z,f)                        annual fuel burn
AnnCO2Emissions(z)               annual CO2 emissions
AnnCurtail(z)                    annual curtailment of generation from renewables
AnnValueG(z,m)                   annual value of thermal generation
AnnValueGByTec(z,i,m)            annual value of thermal generation by technology
AnnValueSIn(z)                   annual value of electricity consumed by storages
AnnValueSOut(z)                  annual value of electricity generated by storages
AnnValueX(z,zz)                  annual value of electricity exports
AnnValueCurtail(z)               annual value of electricity curtailed
AnnCostG(z,i)                    annual cost of thermal generators
AnnRevenueG(z,i)                 annual revenue of thermal generators
AnnProfitG(z,i)                  annual profit of thermal generators
AnnProfitS(z,k)                  annual profit of storages
AnnProfitR(z,n)                  annual profit of renewable generators
AnnSurplusG(z,i)                 annual surplus of thermal generators
AnnProdSurplus(z)                annual producer surplus
AnnSpendingEl(z)                 annual consumer spending on electricity
AnnSpendingHt(z)                 annual consumer spending on heat
AnnSpending(z)                   annual consumer spending on electricity and heat
AvgPriceFuels(z,f)               annual average price of fuels
AvgPriceCO2(z)                   annual average price of CO2 emissions
AvgPriceEl(z)                    annual average price of electricity
AvgPriceHt(z)                    annual average price of heat
HourlyPriceEl(z,t)               hourly price of electricity
HourlyPriceHt(z,t)               hourly price of heat
HourlyPriceSystemServices(z,t)   hourly price of system services
;
* ------------------------------------------------------------------------------
* parameter calculation
AnnRenShare(z) = (sum((t,n), r.L(z,t,n) ) + sum((t,k), s_out.L(z,t,k) ) - sum((t,k), s_in.L(z,t,k) ) + sum((t,i), g.L(z,t,i,'el','Biomass') ) + sum((t,i), g.L(z,t,i,'el','Syngas') ) ) / sum(t, DEMAND(z,t,'el') );
AnnG(z,m) = sum((t,i,f), g.L(z, t, i, m, f));
AnnGByTec(z,i,m,f) = sum(t, g.L(z, t, i, m, f));
AnnGSyngas(z) = sum((t,i), g.L(z,t,i,'el','Syngas') );
AnnGBiomass(z) = sum((t,i), g.L(z,t,i,'el','Biomass') );
AnnGFossil(z) = sum(m, AnnG(z,m)) - AnnGSyngas(z) - AnnGBiomass(z);
AnnR(z) = sum((t,n), r.L(z,t,n) );
AnnSIn(z) = sum((t,k), s_in.L(z,t,k));
AnnSOut(z) = sum((t,k), s_out.L(z,t,k));
AnnCons(z,m) = sum(t, DEMAND(z,t,m));
AnnFullLoadHours(z,n) = sum(t, GEN_PROFILE(z,t,n));
AnnX(zz) = sum(t, x.L('AT',zz,t));
AnnB(z,f) = sum((t,i), b.L(z,t,i,f));
AnnCO2Emissions(z) = sum((t,i), emission_co2.L(z,t,i));
AnnCurtail(z) = sum(t, q_curtail.L(z,t));
AnnValueG(z,m) = sum((t,i,f), bal_el.M(z,t) * g.L(z,t,i,m,f));
AnnValueGByTec(z,i,m) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,m,f));
AnnValueSIn(z) = sum((t,k), bal_el.M(z,t) * s_in.L(z,t,k));
AnnValueSOut(z) = sum((t,k), bal_el.M(z,t) * s_out.L(z,t,k));
AnnValueX(z,zz) = sum(t, bal_el.M(z,t) * x.L(z,zz,t));
AnnValueCurtail(z) = sum(t, bal_el.M(z,t) * q_curtail.L(z,t));
AnnCostG(z,i) = sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) + cost_om_g.L(z,i);
AnnRevenueG(z,i) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,'el',f) + bal_ht.M(z,t) * g.L(z,t,i,'ht',f) );
AnnProfitG(z,i) = AnnRevenueG(z,i) - AnnCostG(z,i);
AnnProfitS(z,k) = sum(t, bal_el.M(z,t) * s_out.L(z,t,k) - bal_el.M(z,t) * s_in.L(z,t,k) );
AnnProfitR(z,n) = sum(t, bal_el.M(z,t) * r.L(z,t,n) ) - cost_om_r.L(z,n);
AnnSurplusG(z,i) = AnnRevenueG(z,i) - sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) - sum((t,m,f), OM_COST_G_VAR(i) * g.L(z,t,i,m,f) );
AnnProdSurplus(z) = sum(i, AnnSurplusG(z,i)) + sum(k, AnnProfitS(z,k)) + sum((t,n), bal_el.M(z,t) * r.L(z,t,n)) - sum((t,n), OM_COST_R_VAR(z,n) * r.L(z,t,n) );
AnnSpendingEl(z) =  sum(t, bal_el.M(z,t) * DEMAND(z,t,'el') );
AnnSpendingHt(z) =  sum(t, bal_ht.M(z,t) * DEMAND(z,t,'ht') );
AnnSpending(z) =  AnnSpendingEl(z) + AnnSpendingHt(z);
AvgPriceFuels(z,f) = sum(t, PRICE_FUEL(z,t,f)) / card(t);
AvgPriceCO2(z) = sum(t, PRICE_CO2(z,t)) / card(t);
AvgPriceEl(z) = sum(t, bal_el.M(z,t))/card(t);
AvgPriceHt(z) = sum(t, bal_ht.M(z,t))/card(t);
HourlyPriceEl(z,t) = bal_el.M(z,t);
HourlyPriceHt(z,t) = bal_ht.M(z,t);
HourlyPriceSystemServices(z,t) = lolim_ancservices.M(z,t);
$offtext
* ==============================================================================
* THE END
* ==============================================================================
