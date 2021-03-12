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
         a                       all energy carriers /wind, gas, electricity, heat, hydrogen /
         e(a)                    energy inputs / wind, gas, electricity, hydrogen, heat /
         m(a)                    final energy / electricity, hydrogen, heat /
         i                       units / turbine, plant, elyzer, psp, hst, chp, e_grid, ht_grid, h2_grid /
         c(i)                    co-generation units / chp /
         d(i)                    dispatchables / plant, elyzer /
         r(i)                    intermittents / turbine /
         s(i)                    storages / psp, hst /
         j(i)                    transmission technologies / e_grid, ht_grid, h2_grid /
         l                       limits of feasible operating regions of CHPs / l1*l4 /
         t                       time / t1*t5 /
         z                       market zones / AT, DE /
;
alias(z,zz);
* ------------------------------------------------------------------------------
PARAMETERS
AIR_POL_COST_FIX(e)              fixed air pollution cost [EUR per MW]
AIR_POL_COST_VAR(e)              variable air pollution cost [EUR per MWh]
CAPACITY(z,i)                    installed capacity of conversion units
CAPACITY_X(z,zz,m)               initial transmission capacity
CAPACITY_STORAGE(z,m,s)          capacity of storage
CAPACITY_STORE_IN(z,m,s)         capacity to store in
CAPACITY_STORE_OUT(z,m,s)        capacity to store out
CAPITALCOST(z,i)                 overnight cost of construction
CAPITALCOST_E(s)                 specific capital cost of storage volume
CAPITALCOST_P(i)                 specific capital cost
CAPITALCOST_X(z,m)               overnight cost of transmission capacity
CONVERSION(e,m,i)                conversion efficiency of technologies
CO2_INTENSITY(e)                 CO2 intensitiy of fuels burned [t CO2 per MWh_th]
COST_OM_QFIX(z,i)                quasi-fixed operation and maintenance cost
COST_OM_VAR(z,i)                 variable operation and maintenance cost
DEMAND(z,t,m)                    demand for product m at time t
DISCOUNT_RATE(z)                 discount rate
DISTANCE(z,zz)                   distance between centers of gravity of market areas [km]
FEASIBLE_INPUT(l,e,c)            relative fuel requirement at corners of feasible operating region
FEASIBLE_OUPUT(l,m,c)            relative energy production at corners of feasible operating region
*INFLOWS(z,t,s)                   energy content of (exogenous) inflows to storages [GW]
LAMBDA                           some parameter
LIFETIME(i)                      technical lifetime of unit
MAP_INPUTS(a,i)                  something else
MAP_OUTPUTS(m,i)                 something
PEAK_LOAD(z)                     maximum electricity load
PEAK_PROFILE(z,e)                maximum supply of intermittent energy
PRICE(z,e)                       price of energy carrier
PRICE_CO2(z,t)                   price of CO2 emissions
PRICE_TRADE(e)                   price of hydrogen and syngas [EUR per MWh]
PROFILE(z,t,e)                   intermittent generation profile
SIGMA                            some parameter
VALUE_NSE(z,m)                   value of non-served energy
;
* ------------------------------------------------------------------------------
* load data
$if %PROJECT% == test $gdxin medea_testing_period
$if %PROJECT% == test $load t
$if %PROJECT% == test $gdxin

$if NOT exist MEDEA_%scenario%_data.gdx  $gdxin medea_main_data
$if     exist MEDEA_%scenario%_data.gdx  $gdxin medea_%scenario%_data
$if NOT %PROJECT% == test $load t
$load    a e m i c d r s j l z
$load
$load
$load
$load
$load
$load
$load
$load
$load
$load
$gdxin

* ------------------------------------------------------------------------------
* calculate annualized capital cost
CAPITALCOST(z,i) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(i) / ((1+DISCOUNT_RATE(z))**LIFETIME(i)-1)*CAPITALCOST_P(i) * 1000;
*CAPITALCOST_V(z,s) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(s) / ((1+DISCOUNT_RATE(z))**LIFETIME(s)-1)*CAPITALCOST_E(s) * 1000;
CAPITALCOST_X(z,m) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME('e_grid') / ((1+DISCOUNT_RATE(z))**LIFETIME('e_grid')-1)*CAPITALCOST_P('e_grid') * 1000;

display CAPITALCOST;

* ------------------------------------------------------------------------------
MAP_OUTPUTS(m,i) = sum(a$CONVERSION(a,m,i), yes);
MAP_INPUTS(a,i) = sum(m$CONVERSION(a,m,i), yes);
display MAP_OUTPUTS, MAP_INPUTS;

* ------------------------------------------------------------------------------
* enable the use of synthetic gas in natural gas-fired plant
$if %SYNGAS% == yes MAP_INPUTS('Syngas',i)$MAP_INPUTS('Gas',i) = 1;
$if %SYNGAS% == yes CONVERSION('Syngas','electricity',i) = CONVERSION('Gas','electricity',i);
$if %SYNGAS% == yes FEASIBLE_INPUT(l,'Syngas',c) = FEASIBLE_INPUT(l,'Gas',c);


AIR_POL_COST_FIX('gas') = 0.1;
AIR_POL_COST_VAR('gas') = 0.5;


table CONVERSION(a,m,i)
                         turbine  plant  elyzer  psp  hst   chp
wind.electricity            1       0      0     0    0      0
gas.electricity             0       0.5    0     0    0      1
electricity.hydrogen        0       0      0.7   0    0      0
electricity.heat            0       0      0.1   0    0      0
electricity.electricity     0       0      0     1    0      0
heat.heat                   0       0      0     0    1      0
gas.heat                    0       0      0     0    0      1
;

table FEASIBLE_OUTPUT(l,m,c)
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

table FEASIBLE_INPUT(l,e,c)
                         chp
l1.gas                    1.64
l2.gas                    1.64
l3.gas                    1.48
l4.gas                    0
;

DEMAND(z,t,'electricity') = 10;
DEMAND('DE',t,'electricity') = 100;
DEMAND(z,t,'heat') = 3;
DEMAND(z,'t4','heat') = 1;
DEMAND(z,t,'hydrogen') = 5;

PROFILE('AT','t1','wind') = 0.3;
PROFILE('AT','t2','wind') = 0.4;
PROFILE('AT','t3','wind') = 0;
PROFILE('AT','t4','wind') = 0.5;
PROFILE('AT','t5','wind') = 200;

PROFILE('DE','t1','wind') = 0.1;
PROFILE('DE','t2','wind') = 0;
PROFILE('DE','t3','wind') = 0.6;
PROFILE('DE','t4','wind') = 0.3;
PROFILE('DE','t5','wind') = 0;

CAPACITY(z,'plant') = 2;
CAPACITY(z,'chp') = 2;

PRICE(z,'gas') = 0.5;
PRICE_CO2(z,t) = 60;

STORAGE_CAPACITY(z,'hydrogen',s) = 8;
STORE_IN_CAPACITY(z,'hydrogen',s) = 4;
STORE_OUT_CAPACITY(z,'hydrogen',s) = 4;

STORAGE_CAPACITY(z,'electricity',s) = 20;
STORE_IN_CAPACITY(z,'electricity',s) = 10;
STORE_OUT_CAPACITY(z,'electricity',s) = 10;

STORAGE_CAPACITY(z,'heat',s) = 5;
STORE_IN_CAPACITY(z,'heat',s) = 1;
STORE_OUT_CAPACITY(z,'heat',s) = 1;

CAPACITY_X(z,zz,m) = 1;

CO2_INTENSITY('gas') = 0.2;

COST_OM_QFIX(z,i) = 10;
COST_OM_VAR(z,i) = 0.01;

VALUE_NSE(z,m) = 12500;

LAMBDA = 0.2;
SIGMA = 0.2;
PEAK_LOAD(z) = SMAX(t,DEMAND(z,t,'electricity'));
PEAK_PROFILE(z,e) = SMAX(t, PROFILE(z,t,e));



* ------------------------------------------------------------------------------
variables
cost                             total system cost
x(z,zz,t,m)                      exchange of energy outputs
;

positive variables
add_x(z,zz,m)                    transmission capacity added
cost_air_pol(z,e)                cost of air pollution
curtail(z,t,m)                   discarded energy output
decommission(z,i)                capacity decommissioned
emission_co2(z,t,e)              quantity of CO2 emitted
fuel_trade(z,t,e)                fuel shipment
gen(z,t,m,i)                     energy generation
invest(z,i)                      capacity investmed
nse(z,t,m)                       non-served energy
storage_content(z,t,m,s)         storage capacity
use(z,t,a,i)                     energy use (endogenous)
w(z,t,c,l,e)                     co-generation weight
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
         sum((z,e,i), sum(t$MAP_INPUTS(e,i), PRICE(z,e) * use(z,t,e,i)) )
         + sum((z,e), sum(t, PRICE_CO2(z,t) * emission_co2(z,t,e) ) )
         + sum((z,i), COST_OM_QFIX(z,i) * (CAPACITY(z,i) + invest(z,i) - decommission(z,i)) + sum((t,m), COST_OM_VAR(z,i) * gen(z,t,m,i) ) )
         + sum((z,i), CAPITALCOST(z,i) * invest(z,i) )
         + sum((z,zz,m), CAPITALCOST_X(z,m) * add_x(z,zz,m) )
         + sum((z,t,m), VALUE_NSE(z,m) * nse(z,t,m) )
;
acc_trade(z)..
         cost_trade(z)
         =E=
         sum((t,e), PRICE_TRADE(e) * fuel_trade(z,t,e) )
;


* ------------------------------------------------------------------------------
* EMISSIONS
* ACCOUNTING FOR EXTERNALITIES FROM AIR POLLUTANTS
acn_airpollute(z,e)..
         cost_air_pol(z,e)
         =E=
         sum(i, AIR_POL_COST_FIX(e) * (CAPACITY(z,i) + invest(z,i) - decommission(z,i)) * MAP_INPUTS(e,i) )
         + sum((t,i), AIR_POL_COST_VAR(e) * use(z,t,e,i) )
;
bal_co2(z,t,e)$CO2_INTENSITY(e)..
                 emission_co2(z,t,e)
                 =E=
                 sum(i, CO2_INTENSITY(e) * use(z,t,e,i))
                 ;
* ------------------------------------------------------------------------------
* SUPPLY DEMAND BALANCE
balance(z,t,m)..
         DEMAND(z,t,m)
         + sum(zz, x(z,zz,t,m) )
         - nse(z,t,m)
         =E=
         sum(i$MAP_OUTPUTS(m,i), gen(z,t,m,i))
*         + fuel_trade(z,t,'Syngas')
         - sum(i$MAP_INPUTS(m,i), use(z,t,m,i))
         - curtail(z,t,m)
;
* ------------------------------------------------------------------------------
* ENERGY CONVERSION
gen.UP(z,t,m,i)$(not MAP_OUTPUTS(m,i)) = 0;
use.UP(z,t,e,i)$(not MAP_INPUTS(e,i)) = 0;

* Capacity Constraint on Energy Output
* * * * does investment raise capacity for all products? * * * *
capacity_constraint(z,t,m,d)$MAP_OUTPUTS(m,d)..
         gen(z,t,m,d)
         =L=
         CAPACITY(z,d) + invest(z,d) - decommission(z,d)
;
* Intermittent Energy Supply
intermittent_generation(z,t,e,r)..
         use(z,t,e,r)
         =E=
         PROFILE(z,t,e) * MAP_INPUTS(e,r) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r))
;
* Energy Conversion With Fixed Efficiency
dispatchable_generation(z,t,m,i)$(MAP_OUTPUTS(m,i) AND NOT c(i) AND NOT s(i))..
         gen(z,t,m,i)
         =E=
         sum(e, CONVERSION(e,m,i) * use(z,t,e,i))
;
* Energy Conversion for Flexible Co-Generation Of Heat And Power
w.UP(z,t,c,l,e)$(NOT FEASIBLE_INPUT(l,e,c)) = 0;
bal_w_chp(z,t,c)..
                 sum((l,e)$(MAP_INPUTS(e,c) ), w(z,t,c,l,e))
                 =L=
                 CAPACITY(z,c) + invest(z,c) - decommission(z,c)
;
uplim_g_chp(z,t,c,m,e)$(MAP_INPUTS(e,c) AND MAP_OUTPUTS(m,c))..
                 gen(z,t,m,c)
                 =E=
                 sum(l$(MAP_INPUTS(e,c) ), FEASIBLE_OUTPUT(l,m,c) * w(z,t,c,l,e))
;
lolim_b_chp(z,t,c,e)$MAP_INPUTS(e,c)..
                 use(z,t,e,c)
                 =E=
                 sum(l$(MAP_INPUTS(e,c) ), FEASIBLE_INPUT(l,e,c) * w(z,t,c,l,e))
;
* ------------------------------------------------------------------------------
* CURTAILMENT OF ENERGY
* might be superfluous
limit_curtail(z,t,m)..
         curtail(z,t,m)
         =L=
         sum(r, gen(z,t,m,r) )
;
* ------------------------------------------------------------------------------
* ENERGY STORAGE
storage_balance(z,t,m,s)..
         storage_content(z,t,m,s)
         =E=
         use(z,t,m,s) - gen(z,t,m,s) + storage_content(z,t-1,m,s)
;
storage_limit(z,t,m,s)..
         storage_content(z,t,m,s)
         =L=
         STORAGE_CAPACITY(z,m,s)
;
store_in_limit(z,t,m,s)..
         use(z,t,m,s)
         =L=
         STORE_IN_CAPACITY(z,m,s) + invest(z,s) - decommission(z,s)
;
store_out_limit(z,t,m,s)..
         gen(z,t,m,s)
         =L=
         STORE_OUT_CAPACITY(z,m,s) + invest(z,s) - decommission(z,s)
;
* ------------------------------------------------------------------------------
* EXCHANGE OF ENERGY OUTPUTS BETWEEN MARKET ZONES
x.FX(z,zz,t,m)$SAMEAS(z,zz) = 0;
x.FX(zz,z,t,m)$SAMEAS(z,zz) = 0;
x.FX(zz,z,t,'heat') = 0;

uplim_transmission(z,zz,t,m)$(NOT SAMEAS(z,zz))..
         x(z,zz,t,m)
         =L=
         CAPACITY_X(z,zz,m) + add_x(z,zz,m)
;
lolim_transmission(z,zz,t,m)$(NOT SAMEAS(z,zz))..
         x(z,zz,t,m)
         =G=
         - (CAPACITY_X(z,zz,m) + add_x(z,zz,m))
;
bal_transmission(z,zz,t,m)$(NOT SAMEAS(z,zz))..
         x(z,zz,t,m)
         =E=
         - x(zz,z,t,m)
;
bal_add_x(z,zz,m)$(NOT SAMEAS(z,zz))..
         add_x(z,zz,m)
         =E=
         add_x(zz,z,m)
;
* ------------------------------------------------------------------------------
* DECOMMISSIONING
decommission.UP(z,i) = CAPACITY(z,i);

* ------------------------------------------------------------------------------
* ANCILLARY SERVICES
ancillary_services(z,t)..
         sum(i$(NOT r(i)), gen(z,t,'electricity',i) )
*         + gen(z,t,'electricity','ror')
         + sum(i, use(z,t,'electricity',i))
         =G=
         LAMBDA * PEAK_LOAD(z)
         + SIGMA * sum(r$(NOT SAMEAS(r,'ror')), sum(e,PEAK_PROFILE(z,e) * MAP_INPUTS(e,r)) * (CAPACITY(z,r) + invest(z,r) - decommission(z,r)) )
;
* ------------------------------------------------------------------------------
* INVESTMENT SWITCHES FOR THE LONG AND THE SHORT RUN
invest.UP(z,i) =  SWITCH_INVEST;
decommission.UP(z,i) = SWITCH_INVEST;


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
         Cost_CO2(z,e)           co2 cost
         Cost_Fuel(z,e,i)        fuel cost
         Cost_Interconnect(z,m)  interconnector transmission cost
         Cost_Invest(z,i)        investment cost
         Cost_OnM(z,i)           operation and maintenance cost
         Cost_Zonal(z)           zonal system cost
;

Cost_CO2(z,e) = sum(t, PRICE_CO2(z,t) * emission_co2.L(z,t,e) );
Cost_Fuel(z,e,i) = sum(t$MAP_INPUTS(e,i), PRICE(z,e) * use.L(z,t,e,i));
Cost_Interconnect(z,m) = sum(zz, CAPITALCOST_X(z,m) * add_x.L(z,zz,m) );
Cost_Invest(z,i) = CAPITALCOST(z,i) * invest.L(z,i);
Cost_OnM(z,i) = COST_OM_QFIX(z,i) * (CAPACITY(z,i) + invest.L(z,i)) + sum((t,m), COST_OM_VAR(z,i) * gen.L(z,t,m,i) );
Cost_Zonal(z) = sum((e,i,m),COST_FUEL(z,e,i) + COST_CO2(z,e) + COST_ONM(z,i) + COST_INVEST(z,i) + COST_INTERCONNECT(z,m) );

display Cost_CO2,Cost_Fuel,Cost_Interconnect,Cost_Invest,Cost_OnM,Cost_Zonal;

parameters
AnnRenShare(z)                   renewables generation divided by electricity consumption
AnnG(z,m)                        annual thermal generation
AnnGByTec(z,i,m,e)               annual thermal generation by technology
AnnGFossil(z)                    annual generation from fossil sources
AnnGSyngas(z)                    annual generation from synthetic gases
AnnGBiomass(z)                   annual generation from biomass
AnnR(z)                          annual generation from renewable sources
AnnSIn(z)                        annual consumption of electricity storages
AnnSOut(z)                       annual generation of electricity storages
AnnCons(z,m)                     annual consumption of electricity and heat
AnnFullLoadHours(z,r)            annual full load hours of renewable technologies
AnnX(z)                          annual electricity exports
AnnB(z,e)                        annual fuel burn
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
AnnProfitS(z,s)                  annual profit of storages
AnnProfitR(z,r)                  annual profit of renewable generators
AnnSurplusG(z,i)                 annual surplus of thermal generators
AnnProdSurplus(z)                annual producer surplus
AnnSpendingEl(z)                 annual consumer spending on electricity
AnnSpendingHt(z)                 annual consumer spending on heat
AnnSpending(z)                   annual consumer spending on electricity and heat
AvgPriceFuels(z,e)               annual average price of fuels
AvgPriceCO2(z)                   annual average price of CO2 emissions
AvgPriceEl(z)                    annual average price of electricity
AvgPriceHt(z)                    annual average price of heat
HourlyPriceEl(z,t)               hourly price of electricity
HourlyPriceHt(z,t)               hourly price of heat
HourlyPriceSystemServices(z,t)   hourly price of system services
;
* ------------------------------------------------------------------------------
* parameter calculation
*AnnRenShare(z) = (sum((t,n), r.L(z,t,n) ) + sum((t,k), s_out.L(z,t,k) ) - sum((t,k), s_in.L(z,t,k) ) + sum((t,i), g.L(z,t,i,'el','Biomass') ) + sum((t,i), g.L(z,t,i,'el','Syngas') ) ) / sum(t, DEMAND(z,t,'el') );
*AnnG(z,m) = sum((t,i,f), g.L(z, t, i, m, f));
*AnnGByTec(z,i,m,f) = sum(t, g.L(z, t, i, m, f));
*AnnGSyngas(z) = sum((t,i), g.L(z,t,i,'el','Syngas') );
*AnnGBiomass(z) = sum((t,i), g.L(z,t,i,'el','Biomass') );
*AnnGFossil(z) = sum(m, AnnG(z,m)) - AnnGSyngas(z) - AnnGBiomass(z);
*AnnR(z) = sum((t,n), r.L(z,t,n) );
*AnnSIn(z) = sum((t,k), s_in.L(z,t,k));
*AnnSOut(z) = sum((t,k), s_out.L(z,t,k));
*AnnCons(z,m) = sum(t, DEMAND(z,t,m));
*AnnFullLoadHours(z,n) = sum(t, GEN_PROFILE(z,t,n));
*AnnX(zz) = sum(t, x.L('AT',zz,t));
*AnnB(z,f) = sum((t,i), b.L(z,t,i,f));
*AnnCO2Emissions(z) = sum((t,i), emission_co2.L(z,t,i));
*AnnCurtail(z) = sum(t, q_curtail.L(z,t));
*AnnValueG(z,m) = sum((t,i,f), bal_el.M(z,t) * g.L(z,t,i,m,f));
*AnnValueGByTec(z,i,m) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,m,f));
*AnnValueSIn(z) = sum((t,k), bal_el.M(z,t) * s_in.L(z,t,k));
*AnnValueSOut(z) = sum((t,k), bal_el.M(z,t) * s_out.L(z,t,k));
*AnnValueX(z,zz) = sum(t, bal_el.M(z,t) * x.L(z,zz,t));
*AnnValueCurtail(z) = sum(t, bal_el.M(z,t) * q_curtail.L(z,t));
*AnnCostG(z,i) = sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) + cost_om_g.L(z,i);
*AnnRevenueG(z,i) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,'el',f) + bal_ht.M(z,t) * g.L(z,t,i,'ht',f) );
*AnnProfitG(z,i) = AnnRevenueG(z,i) - AnnCostG(z,i);
*AnnProfitS(z,k) = sum(t, bal_el.M(z,t) * s_out.L(z,t,k) - bal_el.M(z,t) * s_in.L(z,t,k) );
*AnnProfitR(z,n) = sum(t, bal_el.M(z,t) * r.L(z,t,n) ) - cost_om_r.L(z,n);
*AnnSurplusG(z,i) = AnnRevenueG(z,i) - sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) - sum((t,m,f), OM_COST_G_VAR(i) * g.L(z,t,i,m,f) );
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
