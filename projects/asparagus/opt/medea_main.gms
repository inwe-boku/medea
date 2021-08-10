$title medea

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
         all_tec                 all energy technologies
         f                       fuels
         i(all_tec)              dispatchable energy generation technologies
         h(i)                    power-to-heat technologies
         j(i)                    combined heat and power (CHP) generation technologies
         k(all_tec)              energy storage technologies
         l                       corners of feasible operating regions of CHPs
         m                       energy products (heat and electricity)
         n(all_tec)              intermittent electricity generators
         t                       time periods (hours)
         z                       market zones
;
alias(z,zz);
* ------------------------------------------------------------------------------
Parameters
         AIR_POL_COST_FIX(f)     fixed air pollution cost [EUR per MW]
         AIR_POL_COST_VAR(f)     variable air pollution cost [EUR per MWh]
         CAPITALCOST_P(all_tec)  specific capital cost of dispatchable generators (power) [EUR per MW]
         CAPITALCOST_E(all_tec)  specific capital cost of storage (energy) [EUR per MW]
         CAPITALCOST_G(z,i)      specific annualized capital cost of dispatchable generators [EUR per MW]
         CAPITALCOST_R(z,n)      specific annualized capital cost of intermittent generators [EUR per MW]
         CAPITALCOST_S(z,k)      specific annualized capital cost of storage power (in and out) [EUR per MW]
         CAPITALCOST_V(z,k)      specific annualized capital cost of storage volume [EUR per MWh]
         CAPITALCOST_X(z)        specific annualized capital cost of electricity transmission [EUR per MW]
         CO2_INTENSITY(f)        CO2 intensitiy of fuels burned [t CO2 per MWh_th]
         DEMAND(z,t,m)           energy demand [GW]
         DISCOUNT_RATE(z)        discount rate (WACC)
         DISTANCE(z,zz)          distance between centers of gravity of market areas [km]
         EFFICIENCY_G(i,m,f)     generation efficiency of dispatchable power plants [MWh_el per MWh_th]
         EFFICIENCY_S_OUT(k)     generation efficiency of storages
         EFFICIENCY_S_IN(k)      storing-in efficiency of storages
         FEASIBLE_INPUT(i,l,f)   relative fuel requirement at corners of feasible operating region
         FEASIBLE_OUTPUT(i,l,m)  relative energy production at corners of feasible operating region
         GEN_PROFILE(z,t,n)      generation profile of intermittent sources
         GEN_PROFILE_FUTURE(z,t,n) generation profile of future wind turbines
         INFLOWS(z,t,k)          energy content of (exogenous) inflows to storages [GW]
         INITIAL_CAP_G(z,i)      initial installed capacity of dispatchable generators [GW]
         INITIAL_CAP_R(z,n)      initial installed capacity of intermittent generators [GW]
         INITIAL_CAP_S_OUT(z,k)  initial installed capacity to store-out [GW]
         INITIAL_CAP_S_IN(z,k)   intial installed capacity to store-in [GW]
         INITIAL_CAP_V(z,k)      initial installed storage volume [GWh]
         INITIAL_CAP_X(z,zz)     initial installed transmission capacity [GW]
         LAMBDA(z)               load scaling factor for system service requirement
         LIFETIME(all_tec)       technology lifetime
         MAP_FUEL_G(i,f)         maps fuels to dispatchable plants
         MAP_FUEL_R(n,f)         maps fuels to renewable generators
         OM_COST_G_QFIX(i)       quasi-fixed operation and maintenance cost [EUR per MW]
         OM_COST_G_VAR(i)        variable operation and maintenance cost [EUR per MWh]
         OM_COST_R_QFIX(n)       quasi-fixed operation and maintenance cost [EUR per MW]
         OM_COST_R_VAR(n)        variable operation and maintenance cost [EUR per MWh]
         PEAK_LOAD(z)            maximum electricity demand [GW]
         PEAK_PROFILE(z,n)       maximum relative generation from intermittent sources
         PRICE_CO2(z,t)          CO2 price [EUR per t CO2]
         PRICE_FUEL(z,t,f)       fuel price [EUR per MWh]
         SIGMA(z)                intermittent generation scaling factor for system service requirement
         VALUE_NSE(z)            value of non-served energy [EUR]
         SWITCH_INVEST_THERM     abc
         SWITCH_INVEST_ITM       abc
         SWITCH_INVEST_STORAGE   abc
         SWITCH_INVEST_ATC       cdf
         SWITCH_ANCILLARY        boolean switch for (de)activating the ancillary services equation
;

* ------------------------------------------------------------------------------
* load data
$if %PROJECT% == test $gdxin medea_testing_period
$if %PROJECT% == test $load t
$if %PROJECT% == test $gdxin

$if NOT exist MEDEA_%scenario%_data.gdx  $gdxin medea_main_data
$if     exist MEDEA_%scenario%_data.gdx  $gdxin medea_%scenario%_data
$if NOT %PROJECT% == test $load t
$load    all_tec f i h j k l m n z
$load    AIR_POL_COST_FIX AIR_POL_COST_VAR
$load    CAPITALCOST_P CAPITALCOST_E DISCOUNT_RATE LIFETIME
$load    CO2_INTENSITY DEMAND DISTANCE EFFICIENCY_G EFFICIENCY_S_OUT
$load    EFFICIENCY_S_IN FEASIBLE_INPUT FEASIBLE_OUTPUT GEN_PROFILE GEN_PROFILE_FUTURE INFLOWS
$load    INITIAL_CAP_G INITIAL_CAP_R INITIAL_CAP_S_OUT INITIAL_CAP_S_IN
$load    INITIAL_CAP_V INITIAL_CAP_X LAMBDA OM_COST_G_QFIX OM_COST_G_VAR
$load    OM_COST_R_QFIX OM_COST_R_VAR PRICE_CO2
$load    PEAK_LOAD PEAK_PROFILE PRICE_FUEL SIGMA VALUE_NSE
$load    SWITCH_INVEST_THERM SWITCH_INVEST_ITM SWITCH_INVEST_STORAGE
$load    SWITCH_INVEST_ATC SWITCH_ANCILLARY
$gdxin

MAP_FUEL_G(i,f)$(sum(m,EFFICIENCY_G(i,m,f))) = yes;
MAP_FUEL_R('ror','Water') = yes;
MAP_FUEL_R('pv','Solar') = yes;
MAP_FUEL_R('wind_on','Wind') = yes;
MAP_FUEL_R('wind_off','Wind') = yes;

* ------------------------------------------------------------------------------
* calculate annualized capital cost
CAPITALCOST_G(z,i) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(i) / ((1+DISCOUNT_RATE(z))**LIFETIME(i)-1)*CAPITALCOST_P(i) * 1000;
CAPITALCOST_R(z,n) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(n) / ((1+DISCOUNT_RATE(z))**LIFETIME(n)-1)*CAPITALCOST_P(n) * 1000;
CAPITALCOST_S(z,k) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(k) / ((1+DISCOUNT_RATE(z))**LIFETIME(k)-1)*CAPITALCOST_P(k) * 1000;
CAPITALCOST_V(z,k) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME(k) / ((1+DISCOUNT_RATE(z))**LIFETIME(k)-1)*CAPITALCOST_E(k) * 1000;
CAPITALCOST_X(z) = DISCOUNT_RATE(z)*(1+DISCOUNT_RATE(z))**LIFETIME('transmission') / ((1+DISCOUNT_RATE(z))**LIFETIME('transmission')-1)*CAPITALCOST_P('transmission') * 1000;

display CAPITALCOST_G;

GEN_PROFILE_FUTURE(z,t,'ror') = GEN_PROFILE(z,t,'ror');
GEN_PROFILE_FUTURE(z,t,'pv') = GEN_PROFILE(z,t,'pv');

* ------------------------------------------------------------------------------
* enable the use of synthetic gas in natural gas-fired plant
$if %SYNGAS% == yes MAP_FUEL_G(i,'Syngas')$MAP_FUEL_G(i,'Gas') = yes;
$if %SYNGAS% == yes EFFICIENCY_G(i, 'el', 'Syngas') = EFFICIENCY_G(i, 'el', 'Gas');
$if %SYNGAS% == yes FEASIBLE_INPUT(i,l,'Syngas') = FEASIBLE_INPUT(i,l,'Gas');

* ------------------------------------------------------------------------------
Variables
         cost_system             total system cost [kEUR]
         x(z,zz,t)               (net) commercial electricity exchange between market zones [GW]  # exports are positive - imports negative
;

Positive Variables
         cost_air_pol(z,f)       external cost of air pollution [kEUR]
         cost_fuel(z,t,i)        total cost of fuel used for energy generation [kEUR]
         cost_co2(z,t,i)         total cost of CO2 emissions [kEUR]
         cost_om_g(z,i)          total operation and maintenance cost of dispatchables [kEUR]
         cost_om_r(z,n)          total operation and maintenance cost of intermittents[kEUR]
         cost_zonal(z)           total zonal system cost [kEUR]
         cost_nse(z)             total cost of non-served energy [kEUR]
         cost_invest_g(z)        total investment cost for dispatchable generators [kEUR]
         cost_invest_r(z)        total investment cost for intermittent generators [kEUR]
         cost_invest_sv(z)       total investment cost for storages [kEUR]
         cost_invest_x(z)        total investment cost for transmission capacity [kEUR]
         emission_co2(z,t,i)     bookkeeping of total co2 emissions [kt] # or rather [t]?
         b(z,t,i,f)              fuel used for energy generation [GWh]
         add_g(z,i)              dispatchable generation capacity added [GW]
         add_r(z,n)              intermittent generation capacity added [GW]
         add_s(z,k)              storage capacity (in and out) added [GW]
         add_v(z,k)              storage volume added [GWh]
         add_x(z,zz)             transmission capacity added [GW]
         deco_g(z,i)             dispatchable generation capacity decommissioned [GW]
         deco_r(z,n)             intermittent generation capacity decommissioned [GW]
*         deco_s(z,k)             storage capacity (in and out) decommissioned [GW]
*         deco_v(z,k)             storage volume decommissioned [GWh]
*         deco_x(z,zz)            transmission capacity decommissioned [GW]
         g(z,t,i,m,f)            energy generation by dispatchable generators [GW]
         r(z,t,n)                bookkeeping of electricity generation by intermittent generators [GW]
         s_in(z,t,k)             energy stored-in (flow) [GW]
         s_out(z,t,k)            energy stored-out (flow) [GW]
         v(z,t,k)                energy storage level (stock) [GWh]
         q_curtail(z,t)          curtailed electricity [GW]
         q_nse(z,t,m)            non-served energy [GW]
         w(z,t,i,l,f)            feasible operating region weight
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
objective, bal_zone,
bal_fuel, bal_co2, bal_om_g, bal_om_r, bal_inv_g, bal_inv_r, bal_inv_sv, bal_inv_x, bal_nse,
bal_el, bal_ht,
uplim_g, lolim_b,
bal_w_chp, uplim_g_chp, lolim_b_chp,
acn_itm,
uplim_store_in, uplim_store_out, uplim_store_vol, bal_store, lolim_add_v,
acn_co2,
acn_airpollute,
uplim_transmission, lolim_transmission, bal_transmission, bal_add_x,
uplim_deco_g, uplim_deco_r,
lolim_ancservices,
uplim_curtail
;
* ==============================================================================


* ==============================================================================
* MODEL FORMULATION
* ------------------------------------------------------------------------------
* SYSTEM COST and COST BALANCES

objective..
                 cost_system
                 =E=
                 sum(z, cost_zonal(z))
                 ;
bal_zone(z)..
                 cost_zonal(z)
                 =E=
                 sum((t,i), cost_fuel(z,t,i))
                 + sum((t,i), cost_co2(z,t,i))
                 + sum(i, cost_om_g(z,i))
                 + sum(n, cost_om_r(z,n))
                 + cost_invest_g(z)
                 + cost_invest_r(z)
                 + cost_invest_sv(z)
                 + cost_invest_x(z)
                 + cost_nse(z)
                 ;
bal_fuel(z,t,i)..
                 cost_fuel(z,t,i)
                 =E=
                 sum(f$(MAP_FUEL_G(i,f) ), PRICE_FUEL(z,t,f) * b(z,t,i,f) )
                 ;
bal_co2(z,t,i)..
                 cost_co2(z,t,i)
                 =E=
                 PRICE_CO2(z,t) * emission_co2(z,t,i)
                 ;
bal_om_g(z,i)..
                 cost_om_g(z,i)
                 =E=
                 OM_COST_G_QFIX(i) * (INITIAL_CAP_G(z,i) + add_g(z,i) - deco_g(z,i) )
                 + sum((t,m,f)$(MAP_FUEL_G(i,f) ), OM_COST_G_VAR(i) * g(z,t,i,m,f) )
                 ;
bal_om_r(z,n)..
                 cost_om_r(z,n)
                 =E=
                 OM_COST_R_QFIX(n) * (INITIAL_CAP_R(z,n) + add_r(z,n) - deco_r(z,n) )
                 + sum((t,m), OM_COST_R_VAR(n) * r(z,t,n) )
                 ;
bal_inv_g(z)..
                 cost_invest_g(z)
                 =E=
                 sum(i, CAPITALCOST_G(z,i) * add_g(z,i) )
                 ;
bal_inv_r(z)..
                 cost_invest_r(z)
                 =E=
                 sum(n, CAPITALCOST_R(z,n) * add_r(z,n) )
                 ;
bal_inv_sv(z)..
                 cost_invest_sv(z)
                 =E=
                 sum(k, CAPITALCOST_S(z,k) * add_s(z,k)
                 + CAPITALCOST_V(z,k) * add_v(z,k) )
                 ;
bal_inv_x(z)..
                 cost_invest_x(z)
                 =E=
                 0.5 * sum(zz, CAPITALCOST_X(z) * DISTANCE(z,zz) * add_x(z,zz) )
                 ;
bal_nse(z)..
                 cost_nse(z)
                 =E=
                 sum((t,m), VALUE_NSE(z) * q_nse(z,t,m) )
                 ;
* ------------------------------------------------------------------------------
* MARKET CLEARING

bal_el(z,t)..
                 sum((i,f)$(MAP_FUEL_G(i,f) ), g(z,t,i,'el',f) )
                 + sum(n, r(z,t,n) )
                 + sum(k, s_out(z,t,k) )
                 - q_curtail(z,t)
                 =E=
                 DEMAND(z,t,'el')
                 + sum(i, b(z,t,i,'Power') )
                 + sum(k, s_in(z,t,k) )
                 + sum(zz, x(z,zz,t) )
                 - q_nse(z,t,'el')
                 ;
bal_ht(z,t)..
                 sum((i,f)$(MAP_FUEL_G(i,f) ), g(z,t,i,'ht',f) )
                 =E=
                 DEMAND(z,t,'ht')
                 - q_nse(z,t,'ht')
                 ;
* ------------------------------------------------------------------------------
* CONVENTIONAL ELECTRICITY GENERATION

* set efficiency for electricity-only gas plants

uplim_g(z,t,i,m)..
                 sum(f$(MAP_FUEL_G(i,f) ), g(z,t,i,m,f) )
                 =L=
                 INITIAL_CAP_G(z,i) + add_g(z,i) - deco_g(z,i)
                 ;
lolim_b(z,t,i,m,f)$(NOT j(i))..
                 g(z,t,i,m,f)
                 =E=
                 EFFICIENCY_G(i,m,f) * b(z,t,i,f)
                 ;
b.UP(z,t,i,f)$(NOT MAP_FUEL_G(i,f)) = 0;
* ------------------------------------------------------------------------------
* CO-GENERATION OF HEAT AND ELECTRICITY

* set kennlinienfeld for gas chps

bal_w_chp(z,t,i)$(j(i))..
                 sum((l,f)$(MAP_FUEL_G(i,f) ), w(z,t,i,l,f))
                 =L=
                 INITIAL_CAP_G(z,i) + add_g(z,i) - deco_g(z,i)
                 ;
uplim_g_chp(z,t,i,m,f)$(j(i))..
                 g(z,t,i,m,f)
                 =E=
                 sum(l$(MAP_FUEL_G(i,f) ), FEASIBLE_OUTPUT(i,l,m) * w(z,t,i,l,f) )
                 ;
lolim_b_chp(z,t,i,f)$(j(i))..
                 b(z,t,i,f)
                 =E=
                 sum(l$(MAP_FUEL_G(i,f) ), FEASIBLE_INPUT(i,l,f) * w(z,t,i,l,f) )
                 ;
w.UP(z,t,i,l,f)$(NOT FEASIBLE_INPUT(i,l,f)) = 0;
* ------------------------------------------------------------------------------
* INTERMITTENT ELECTRICITY GENERATION

acn_itm(z,t,n)..
                 r(z,t,n)
                 =E=
                 GEN_PROFILE(z,t,n) * (INITIAL_CAP_R(z,n) - deco_r(z,n) )
                 + add_r(z,n) * GEN_PROFILE_FUTURE(z,t,n)
                 ;
* ------------------------------------------------------------------------------
* ELECTRICITY STORAGE

uplim_store_in(z,t,k)..
                 s_out(z,t,k)
                 =L=
                 INITIAL_CAP_S_OUT(z,k) + add_s(z,k)
                 ;
uplim_store_out(z,t,k)..
                 s_in(z,t,k)
                 =L=
                 INITIAL_CAP_S_IN(z,k) + add_s(z,k)
                 ;
uplim_store_vol(z,t,k)..
                 v(z,t,k)
                 =L=
                 INITIAL_CAP_V(z,k) + add_v(z,k)
                 ;
bal_store(z,t,k)$(ord(t) > 1 AND EFFICIENCY_S_OUT(k))..
                 v(z,t,k)
                 =E=
                 INFLOWS(z,t,k)
                 + EFFICIENCY_S_IN(k) * s_in(z,t,k)
                 - (1 / EFFICIENCY_S_OUT(k))  * s_out(z,t,k)
                 + v(z,t-1,k)
                 ;
lolim_add_v(z,k)..
                 add_v(z,k)
                 =G=
                 add_s(z,k)
                 ;
v.FX(z,t,k)$(ord(t)=1) = 0.6 * INITIAL_CAP_V(z,k);
v.FX(z,t,k)$(ord(t) eq card(t)) = 0.6 * INITIAL_CAP_V(z,k);
* ------------------------------------------------------------------------------
* CO2 ACCOUNTING

acn_co2(z,t,i)..
                 emission_co2(z,t,i)
                 =E=
                 sum(f$(CO2_INTENSITY(f)), CO2_INTENSITY(f) * b(z,t,i,f) )
                 ;
* ------------------------------------------------------------------------------
* ACCOUNTING FOR EXTERNALITIES FROM AIR POLLUTANTS

acn_airpollute(z,f)..
                 cost_air_pol(z,f)
                 =E=
                 sum(i$MAP_FUEL_G(i,f), AIR_POL_COST_FIX(f) * (INITIAL_CAP_G(z,i) + add_g(z,i) - deco_g(z,i)) * MAP_FUEL_G(i,f))
                 + sum(n$MAP_FUEL_R(n,f), AIR_POL_COST_FIX(f) * (INITIAL_CAP_R(z,n) + add_r(z,n) - deco_r(z,n)) * MAP_FUEL_R(n,f))
                 + sum((t,i)$MAP_FUEL_G(i,f), AIR_POL_COST_VAR(f) * b(z,t,i,f))
                 + sum((t,n)$MAP_FUEL_R(n,f), AIR_POL_COST_VAR(f) * r(z,t,n) * MAP_FUEL_R(n,f) )
                 ;

* ------------------------------------------------------------------------------
* INTERZONAL ELECTRICITY EXCHANGE

uplim_transmission(z,zz,t)..
                 x(z,zz,t)
                 =L=
                 INITIAL_CAP_X(z,zz) + add_x(z,zz)
                 ;
lolim_transmission(z,zz,t)..
                 x(z,zz,t)
                 =G=
                 - (INITIAL_CAP_X(z,zz) + add_x(z,zz) )
                 ;
bal_transmission(z,zz,t)..
                 x(z,zz,t)
                 =E=
                 - x(zz,z,t)
                 ;
bal_add_x(z,zz)..
                 add_x(z,zz)
                 =E=
                 add_x(zz,z)
                 ;
x.FX(z,zz,t)$(not INITIAL_CAP_X(z,zz)) = 0;
x.FX(zz,z,t)$(not INITIAL_CAP_X(zz,z)) = 0;
* ------------------------------------------------------------------------------
* DECOMMISSIONING

uplim_deco_g(z,i)..
                 deco_g(z,i)
                 =L=
                 INITIAL_CAP_G(z,i) + add_g(z,i)
                 ;
uplim_deco_r(z,n)..
                 deco_r(z,n)
                 =L=
                 INITIAL_CAP_R(z,n)
*                + add_r(z,n)
                 ;
* ------------------------------------------------------------------------------
* ANCILLARY SERVICES

lolim_ancservices(z,t)$(SWITCH_ANCILLARY)..
                 sum((i,f)$(MAP_FUEL_G(i,f) ), g(z,t,i,'el',f) )
                 + r(z,t,'ror')
                 + sum(k, s_out(z,t,k) + s_in(z,t,k) )
                 =G=
                 LAMBDA(z) * PEAK_LOAD(z)
                 + SIGMA(z) * sum(n$(NOT SAMEAS(n,'ror')), PEAK_PROFILE(z,n) * (INITIAL_CAP_R(z,n) + add_r(z,n) ) )
                 ;
* ------------------------------------------------------------------------------
* CURTAILMENT

uplim_curtail(z,t)..
                 sum(n$(NOT SAMEAS(n,'ror')), r(z,t,n) )
                 =G=
                 q_curtail(z,t)
                 ;
* ------------------------------------------------------------------------------
* INVESTMENT SWITCHES FOR THE LONG AND THE SHORT RUN

add_g.UP(z,i) =  SWITCH_INVEST_THERM;
deco_g.UP(z,i) = SWITCH_INVEST_THERM;
add_r.UP(z,n) =  SWITCH_INVEST_ITM(z, n);
add_s.UP(z,k) =  SWITCH_INVEST_STORAGE(z, k);
add_v.UP(z,k) =  SWITCH_INVEST_STORAGE(z, k);
add_x.UP(z,zz) = 5 * SWITCH_INVEST_ATC(z,zz) * INITIAL_CAP_X(z,zz);
* ==============================================================================


* ==============================================================================
* project control
* ------------------------------------------------------------------------------
$if set PROJECT $include medea_%PROJECT%.gms
* ==============================================================================

model medea / all /;

options
solvelink = 0,
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
memoryemphasis 1
names no
lpmethod 4
$offecho
medea.OptFile = 1;

* ==============================================================================

solve medea using LP minimizing cost_system;


* ==============================================================================
* REPORTING

* ------------------------------------------------------------------------------
* solve details
scalars modelStat, solveStat;
modelStat = medea.modelstat;
solveStat = medea.solvestat;

* ------------------------------------------------------------------------------
* EX-POST ANALYSIS
* parameters summarizing model solution - CamelCaseStyle beginning with Ann
parameters
AirPollutionCost(z)              total cost of air pollution
AnnRenShare(z)                   renewables generation divided by electricity consumption
AnnG(z,m)                        annual thermal generation
AnnGByTec(z,i,m,f)               annual thermal generation by technology
AnnGFossil(z)                    annual generation from fossil sources
AnnGSyngas(z)                    annual generation from synthetic gases
AnnGBiomass(z)                   annual generation from biomass
AnnR(z)                          annual generation from intermittent sources
AnnRenew(z)                      annual generation from renewable sources
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
AnnValueI(z,zz)                  annual value of electricity imports
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
CostCO2(z)                       annual cost of CO2 emissions
CostFuel(z)                      annual cost of fuel
CostOMG(z)                       annual O&M cost of dispatchable generators
CostOMR(z)                       annual O&M cost of intermittent generators
;
* ------------------------------------------------------------------------------
* parameter calculation
AirPollutionCost(z) = sum(f, cost_air_pol.L(z,f));
AnnRenShare(z) = (sum((t,n), r.L(z,t,n) ) + sum((t,k), s_out.L(z,t,k) ) - sum((t,k), s_in.L(z,t,k) ) + sum((t,i), g.L(z,t,i,'el','Biomass') ) ) / sum(t, DEMAND(z,t,'el') );  # + sum((t,i), g.L(z,t,i,'el','Syngas') ) ) / sum(t, DEMAND(z,t,'el') );
AnnG(z,m) = sum((t,i,f), g.L(z, t, i, m, f));
AnnGByTec(z,i,m,f) = sum(t, g.L(z, t, i, m, f));
*AnnGSyngas(z) = sum((t,i), g.L(z,t,i,'el','Syngas') );
AnnGBiomass(z) = sum((t,i), g.L(z,t,i,'el','Biomass') );
AnnGFossil(z) = sum(m, AnnG(z,m)) - AnnGBiomass(z);  # - AnnGSyngas(z)
AnnR(z) = sum((t,n), r.L(z,t,n) );
AnnRenew(z) = AnnR(z) + AnnGBiomass(z) + sum((t,k), INFLOWS(z,t,k)*EFFICIENCY_S_OUT(k));
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
AnnValueX('AT',zz) = sum(t$(x.L('AT',zz,t) > 0), bal_el.M(zz,t) * x.L('AT',zz,t));
AnnValueX('DE',zz) = sum(t$(x.L('DE',zz,t) > 0), bal_el.M(zz,t) * x.L('DE',zz,t));
AnnValueI('AT',zz) = sum(t$(x.L('AT',zz,t) < 0), bal_el.M('AT',t) * x.L('AT',zz,t));
AnnValueI('DE',zz) = sum(t$(x.L('DE',zz,t) < 0), bal_el.M('DE',t) * x.L('DE',zz,t));
AnnValueCurtail(z) = sum(t, bal_el.M(z,t) * q_curtail.L(z,t));
AnnCostG(z,i) = sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) + cost_om_g.L(z,i);
AnnRevenueG(z,i) = sum((t,f), bal_el.M(z,t) * g.L(z,t,i,'el',f) + bal_ht.M(z,t) * g.L(z,t,i,'ht',f) );
AnnProfitG(z,i) = AnnRevenueG(z,i) - AnnCostG(z,i);
AnnProfitS(z,k) = sum(t, bal_el.M(z,t) * s_out.L(z,t,k) - bal_el.M(z,t) * s_in.L(z,t,k) );
AnnProfitR(z,n) = sum(t, bal_el.M(z,t) * r.L(z,t,n) ) - cost_om_r.L(z,n);
AnnSurplusG(z,i) = AnnRevenueG(z,i) - sum(t, cost_fuel.L(z,t,i) + cost_co2.L(z,t,i) ) - sum((t,m,f), OM_COST_G_VAR(i) * g.L(z,t,i,m,f) );
AnnProdSurplus(z) = sum(i, AnnSurplusG(z,i)) + sum(k, AnnProfitS(z,k)) + sum((t,n), bal_el.M(z,t) * r.L(z,t,n)) - sum((t,n), OM_COST_R_VAR(n) * r.L(z,t,n) );
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
CostCO2(z) = sum((t,i), cost_co2.L(z,t,i)) ;
CostFuel(z) = sum((t,i), cost_fuel.L(z,t,i));
CostOMG(z) = sum((i), cost_om_g.L(z,i));
CostOMR(z) = sum((n), cost_om_r.L(z,n));

* ==============================================================================
* THE END
* ==============================================================================
* this line intentionally left blank
