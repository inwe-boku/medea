$title medea
* medea - a multiproduct electricity sector model
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

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* TO-DO
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* - enable fuel trade in supply-demand balance


* ==============================================================================
* SYMBOL DECLARATIONS
* ------------------------------------------------------------------------------
sets
         e                       all energy carriers - prev "a" / wind, gas, electricity, heat, hydrogen /
         i(e)                    energy inputs - prev "e(a)"    / wind, gas, electricity, hydrogen, heat /
         f(e)                    final energy - prev "m(a)"     / electricity, hydrogen, heat /
t                                units - prev "i"               / turbine, plant, elyzer, psp, hst, chp, e_grid, ht_grid, h2_grid /
         c(t)                    co-generation units            / chp /
         d(t)                    dispatchables                  / plant, elyzer /
         r(t)                    intermittents                  / turbine /
         s(t)                    storages                       / psp, hst /
*g(t)         j(i)                    transmission technologies / e_grid, ht_grid, h2_grid /
         l                       limits of feasible operating regions of CHPs / l1*l4 /
         h                       time \ hours - prev "t"        / h1*h5 /
         z                       market zones                   / AT, DE /
;
alias(z,zz);
* ------------------------------------------------------------------------------
PARAMETERS
AIR_POL_COST_FIX(i)              fixed air pollution cost [EUR per MW]
AIR_POL_COST_VAR(i)              variable air pollution cost [EUR per MWh]
CAPACITY(z,t)                    installed capacity of conversion units
CAPACITY_X(z,zz,f)               initial transmission capacity
CAPACITY_STORAGE(z,f,s)          capacity of storage
CAPACITY_STORE_IN(z,f,s)         capacity to store in
CAPACITY_STORE_OUT(z,f,s)        capacity to store out
CAPITALCOST(z,t)                 overnight cost of construction
CAPITALCOST_E(s)                 specific capital cost of storage volume
CAPITALCOST_P(t)                 specific capital cost
CAPITALCOST_X(z,f)               overnight cost of transmission capacity
CONVERSION(e,f,t)                conversion efficiency of technologies
CO2_INTENSITY(i)                 CO2 intensitiy of fuels burned [t CO2 per MWh_th]
COST_OM_QFIX(z,t)                quasi-fixed operation and maintenance cost
COST_OM_VAR(z,t)                 variable operation and maintenance cost
DEMAND(z,h,f)                    demand for product m at time t
DISCOUNT_RATE(z)                 discount rate
DISTANCE(z,zz)                   distance between centers of gravity of market areas [km]
FEASIBLE_INPUT(l,i,c)            relative fuel requirement at corners of feasible operating region
FEASIBLE_OUPUT(l,f,c)            relative energy production at corners of feasible operating region
INFLOWS(z,h,s)                   energy content of (exogenous) inflows to storages [GW]
LAMBDA(z)                        some parameter
LIFETIME(t)                      technical lifetime of unit
MAP_INPUTS(e,t)                  something else
MAP_OUTPUTS(f,t)                 something
PEAK_LOAD(z)                     maximum electricity load
PEAK_PROFILE(z,i)                maximum supply of intermittent energy
PRICE(z,h,i)                     price of energy carrier
PRICE_CO2(z,h)                   price of CO2 emissions
PRICE_TRADE(i)                   price of hydrogen and syngas [EUR per MWh]
PROFILE(z,h,i)                   intermittent generation profile
SIGMA                            some parameter
SWITCH_INVEST                    switches between long-term and short-term perspective
VALUE_NSE(z,f)                   value of non-served energy
;
* ------------------------------------------------------------------------------
* load data
*$if %PROJECT% == test $gdxin medea_testing_period
**$if %PROJECT% == test $load t
*$if %PROJECT% == test $gdxin
*
*$if NOT exist MEDEA_%scenario%_data.gdx  $gdxin medea_main_data
*$if     exist MEDEA_%scenario%_data.gdx  $gdxin medea_%scenario%_data
*$if NOT %PROJECT% == test $load t
*$load    a e m i c d r s j l z
*$load    AIR_POL_COST_FIX AIR_POL_COST_VAR CAPACITY CAPACITY_X CAPACITY_STORAGE
*$load    CAPACITY_STORE_IN CAPACITY_STORE_OUT CAPITALCOST CAPITALCOST_E
*$load    CAPITALCOST_P CAPITALCOST_X CONVERSION CO2_INTENSITY COST_OM_QFIX
*$load    COST_OM_VAR DEMAND DISCOUNT_RATE DISTANCE FEASIBLE_INPUT FEASIBLE_OUPUT
*$load    INFLOWS LAMBDA LIFETIME MAP_INPUTS MAP_OUTPUTS PEAK_LOAD PEAK_PROFILE
*$load    PRICE PRICE_CO2 PRICE_TRADE PROFILE SIGMA SWITCH_INVEST VALUE_NSE
*$gdxin

SWITCH_INVEST = 100;
PRICE_TRADE(i) = 100000;

table CONVERSION(e,f,t)
                         turbine  plant  elyzer  psp  hst   chp
wind.electricity            1       0      0     0    0      0
gas.electricity             0       0.5    0     0    0      1
electricity.hydrogen        0       0      0.7   0    0      0
electricity.heat            0       0      0.1   0    0      0
electricity.electricity     0       0      0     1    0      0
heat.heat                   0       0      0     0    1      0
gas.heat                    0       0      0     0    0      1
;

table FEASIBLE_OUTPUT(l,f,c)
                         chp
l1.electricity            1
l2.electricity            0.9055
l3.electricity            0.8055
l4.electricity            0
l1.heat                   0
l2.heat                   0.63
l3.heat                   0.63
l4.heat                   0
;

table FEASIBLE_INPUT(l,i,c)
                         chp
l1.gas                    1.64
l2.gas                    1.64
l3.gas                    1.48
l4.gas                    0
;

* ------------------------------------------------------------------------------
* calculate annualized capital cost
DISCOUNT_RATE(z) = 0.05;
LIFETIME(t) = 25;
CAPITALCOST_P(t) = 1000;
CAPITALCOST(z,t) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(t) / ((1+DISCOUNT_RATE(z))**LIFETIME(t)-1)*CAPITALCOST_P(t) * 1000;
*CAPITALCOST_V(z,s) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(s) / ((1+DISCOUNT_RATE(z))**LIFETIME(s)-1)*CAPITALCOST_E(s) * 1000;
CAPITALCOST_X(z,f) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME('e_grid') / ((1+DISCOUNT_RATE(z))**LIFETIME('e_grid')-1)*CAPITALCOST_P('e_grid') * 1000;

display CAPITALCOST;

* ------------------------------------------------------------------------------
MAP_OUTPUTS(f,t) = sum(e$CONVERSION(e,f,t), yes);
MAP_INPUTS(e,t) = sum(f$CONVERSION(e,f,t), yes);
display MAP_OUTPUTS, MAP_INPUTS;

* ------------------------------------------------------------------------------
* enable the use of synthetic gas in natural gas-fired plant
$if %SYNGAS% == yes MAP_INPUTS('Syngas',t)$MAP_INPUTS('Gas',t) = 1;
$if %SYNGAS% == yes CONVERSION('Syngas','electricity',t) = CONVERSION('Gas','electricity',t);
$if %SYNGAS% == yes FEASIBLE_INPUT(l,'Syngas',c) = FEASIBLE_INPUT(l,'Gas',c);


AIR_POL_COST_FIX('gas') = 0.1;
AIR_POL_COST_VAR('gas') = 0.5;


DEMAND(z,h,'electricity') = 10;
DEMAND('DE',h,'electricity') = 100;
DEMAND(z,h,'heat') = 3;
DEMAND(z,'h4','heat') = 1;
DEMAND(z,h,'hydrogen') = 5;

PROFILE('AT','h1','wind') = 0.3;
PROFILE('AT','h2','wind') = 0.4;
PROFILE('AT','h3','wind') = 0;
PROFILE('AT','h4','wind') = 0.5;
PROFILE('AT','h5','wind') = 200;

PROFILE('DE','h1','wind') = 0.1;
PROFILE('DE','h2','wind') = 0;
PROFILE('DE','h3','wind') = 0.6;
PROFILE('DE','h4','wind') = 0.3;
PROFILE('DE','h5','wind') = 0;

CAPACITY(z,'plant') = 2;
CAPACITY(z,'chp') = 2;

PRICE(z,'gas') = 0.5;
PRICE_CO2(z,h) = 60;

CAPACITY_STORAGE(z,'hydrogen',s) = 8;
CAPACITY_STORE_IN(z,'hydrogen',s) = 4;
CAPACITY_STORE_OUT(z,'hydrogen',s) = 4;

CAPACITY_STORAGE(z,'electricity',s) = 20;
CAPACITY_STORE_IN(z,'electricity',s) = 10;
CAPACITY_STORE_OUT(z,'electricity',s) = 10;

CAPACITY_STORAGE(z,'heat',s) = 5;
CAPACITY_STORE_IN(z,'heat',s) = 1;
CAPACITY_STORE_OUT(z,'heat',s) = 1;

CAPACITY_X(z,zz,f) = 1;

CO2_INTENSITY('gas') = 0.2;

COST_OM_QFIX(z,t) = 10;
COST_OM_VAR(z,t) = 0.01;

VALUE_NSE(z,f) = 12500;

LAMBDA = 0.2;
SIGMA = 0.2;
PEAK_LOAD(z) = SMAX(h,DEMAND(z,h,'electricity'));
PEAK_PROFILE(z,i) = SMAX(h, PROFILE(z,h,i));



* ------------------------------------------------------------------------------
variables
cost                             total system cost
x(z,zz,h,f)                      exchange of energy outputs
;

positive variables
add_x(z,zz,f)                    transmission capacity added
cost_air_pol(z,i)                cost of air pollution
cost_trade(z)                    cost of trade in syn fuels
curtail(z,h,f)                   discarded energy output
decommission(z,t)                capacity decommissioned
emission_co2(z,h,i)              quantity of CO2 emitted
fuel_trade(z,h,i)                fuel shipment
gen(z,h,f,t)                     energy generation
invest(z,t)                      capacity investmed
nse(z,h,f)                       non-served energy
storage_content(z,h,f,s)         storage capacity
use(z,h,e,t)                     energy use (endogenous)
w(z,h,c,l,i)                     co-generation weight
;

* ------------------------------------------------------------------------------
equations
objective,acc_trade,
balance, intermittent_generation, dispatchable_generation, capacity_constraint,
storage_balance,storage_limit,store_in_limit,store_out_limit,
bal_w_chp,uplim_g_chp,lolim_b_chp,
uplim_transmission,lolim_transmission,bal_transmission,bal_add_x,
bal_co2, acn_airpollute,limit_curtail,ancillary_services
;

* THINGS TO ADD:
* - investment in storage capacity
* - derived post-solution variables
* - switches for different model options (short-run/long-run, ancillary services, ...) **** better to implement in python
* - spatially resolved investment in plants / nodes or cells


* ------------------------------------------------------------------------------
* TOTAL SYSTEM COST AND ITS COMPONENTS
objective..
         cost
         =E=
         sum((z,i,t), sum(h$MAP_INPUTS(i,t), PRICE(z,i) * use(z,h,i,t)) )
         + sum((z,i), sum(h, PRICE_CO2(z,h) * emission_co2(z,h,i) ) )
         + sum((z,t), COST_OM_QFIX(z,t) * (CAPACITY(z,t) + invest(z,t) - decommission(z,t)) + sum((h,f), COST_OM_VAR(z,t) * gen(z,h,f,t) ) )
         + sum((z,t), CAPITALCOST(z,t) * invest(z,t) )
         + sum((z,zz,f), CAPITALCOST_X(z,f) * add_x(z,zz,f) )
         + sum((z,h,f), VALUE_NSE(z,f) * nse(z,h,f) )
;
acc_trade(z)..
         cost_trade(z)
         =E=
         sum((h,i), PRICE_TRADE(i) * fuel_trade(z,h,i) )
;


* ------------------------------------------------------------------------------
* EMISSIONS
* ACCOUNTING FOR EXTERNALITIES FROM AIR POLLUTANTS
acn_airpollute(z,i)..
         cost_air_pol(z,i)
         =E=
         sum(t, AIR_POL_COST_FIX(i) * (CAPACITY(z,t) + invest(z,t) - decommission(z,t)) * MAP_INPUTS(i,t) )
         + sum((h,t), AIR_POL_COST_VAR(i) * use(z,h,i,t) )
;
bal_co2(z,h,i)$CO2_INTENSITY(i)..
                 emission_co2(z,h,i)
                 =E=
                 sum(t, CO2_INTENSITY(i) * use(z,h,i,t))
                 ;
* ------------------------------------------------------------------------------
* SUPPLY DEMAND BALANCE
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
gen.UP(z,h,f,t)$(not MAP_OUTPUTS(f,t)) = 0;
use.UP(z,h,i,t)$(not MAP_INPUTS(i,t)) = 0;

* Capacity Constraint on Energy Output
* * * * does investment raise capacity for all products? * * * *
capacity_constraint(z,h,f,d)$MAP_OUTPUTS(f,d)..
         gen(z,h,f,d)
         =L=
         CAPACITY(z,d) + invest(z,d) - decommission(z,d)
;
* Intermittent Energy Supply
intermittent_generation(z,h,i,r)..
         use(z,h,i,r)
         =E=
         PROFILE(z,h,i) * MAP_INPUTS(i,r) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r))
;
* Energy Conversion With Fixed Efficiency
dispatchable_generation(z,h,f,t)$(MAP_OUTPUTS(f,t) AND NOT c(t) AND NOT s(t))..
         gen(z,h,f,t)
         =E=
         sum(i, CONVERSION(i,f,t) * use(z,h,i,t))
;
* Energy Conversion for Flexible Co-Generation Of Heat And Power
w.UP(z,h,c,l,i)$(NOT FEASIBLE_INPUT(l,i,c)) = 0;
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
limit_curtail(z,h,f)..
         curtail(z,h,f)
         =L=
         sum(r, gen(z,h,f,r) )
;
* ------------------------------------------------------------------------------
* ENERGY STORAGE
storage_balance(z,h,f,s)..
         storage_content(z,h,f,s)
         =E=
         use(z,h,f,s) - gen(z,h,f,s) + storage_content(z,h-1,f,s)
;
storage_limit(z,h,f,s)..
         storage_content(z,h,f,s)
         =L=
         CAPACITY_STORAGE(z,f,s)
;
store_in_limit(z,h,f,s)..
         use(z,h,f,s)
         =L=
         CAPACITY_STORE_IN(z,f,s) + invest(z,s) - decommission(z,s)
;
store_out_limit(z,h,f,s)..
         gen(z,h,f,s)
         =L=
         CAPACITY_STORE_OUT(z,f,s) + invest(z,s) - decommission(z,s)
;
* ------------------------------------------------------------------------------
* EXCHANGE OF ENERGY OUTPUTS BETWEEN MARKET ZONES
x.FX(z,zz,h,f)$SAMEAS(z,zz) = 0;
x.FX(zz,z,h,f)$SAMEAS(z,zz) = 0;
x.FX(zz,z,h,'heat') = 0;

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
* DECOMMISSIONING
decommission.UP(z,t) = CAPACITY(z,t);

* ------------------------------------------------------------------------------
* ANCILLARY SERVICES
ancillary_services(z,h)..
         sum(t$(NOT r(t)), gen(z,h,'electricity',t) )
*         + gen(z,h,'electricity','ror')
         + sum(t, use(z,h,'electricity',t))
         =G=
         LAMBDA(z) * PEAK_LOAD(z)
         + SIGMA * sum(r$(NOT SAMEAS(r,'ror')), sum(i,PEAK_PROFILE(z,i) * MAP_INPUTS(i,r)) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r)) )
;
* ------------------------------------------------------------------------------
* INVESTMENT SWITCHES FOR THE LONG AND THE SHORT RUN
invest.UP(z,t) =  SWITCH_INVEST;
decommission.UP(z,t) = SWITCH_INVEST;


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

$onecho > cplex.opt
lpmethod 4
names no
$offecho
medea.OptFile = 1;

solve medea using LP minimizing cost;

* ------------------------------------------------------------------------------
* SOLVE DETAILS
scalars modelStat, solveStat;
modelStat = medea.modelstat;
solveStat = medea.solvestat;

* ------------------------------------------------------------------------------
* POST-SOLUTION PARAMETERS
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
