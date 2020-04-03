$title add-on to medea_main.gms to include custom model modifications

* example: modification of CO2 price
* ------------------------------------------------------------------------------

* generate scenario parameter -- same parameter must be included in medea_%scenario%_data.gdx
parameters
         CO2_SCENARIO            scenario emission allowance price
         WIND_ON_LIMIT           upper limit on onshore wind deployment
         FLOW_LIMIT              upper limit on electricity exchange
         PV_CAPEX                annuity of PV capex
;

* read scenario parameter from scenario .gdx-file
$gdxin medea_%scenario%_data
$load  CO2_SCENARIO WIND_ON_LIMIT FLOW_LIMIT PV_CAPEX
$gdxin

* set model parameter to scenario parameter value
PRICE_CO2(z,t) = CO2_SCENARIO;
CAPITALCOST_R(z,'pv') = PV_CAPEX;

add_r.UP('AT','wind_on') = WIND_ON_LIMIT;
add_r.UP('AT','pv') = 80;
add_g.UP('AT','nuc') = 0;
add_g.UP('AT','bio') = 0;
add_g.UP('AT','bio_chp') = 0;
add_g.UP('DE','nuc') = 0;
add_g.UP('DE','bio') = 1;
add_g.UP('DE','bio_chp') = 1;

x.UP(z,zz,t) = FLOW_LIMIT;
x.LO(z,zz,t) = -FLOW_LIMIT;
* no transmission from region to itself
x.FX(z,zz,t)$(not INITIAL_CAP_X(z,zz)) = 0;
x.FX(zz,z,t)$(not INITIAL_CAP_X(zz,z)) = 0;

* ------------------------------------------------------------------------------
* policy constraints
* ------------------------------------------------------------------------------

equations
         policy_100resbalance    policy constraint requiring "100%" renewable electricity generation over year
;
* ------------------------------------------------------------------------------

policy_100resbalance..
         sum((t,n), GEN_PROFILE('AT',t,n) * (INITIAL_CAP_R('AT',n) + add_r('AT',n) ) )
         + sum(t, g('AT',t,'bio_chp','el','biomass'))
         + sum(t, g('AT',t,'bio','el','biomass'))
         + sum((t,k), s_out('AT',t,k))
         - sum((t,k), s_in('AT',t,k) * EFFICIENCY_S_IN('AT',k))
         =G=
         0.90 * sum(t, DEMAND('AT',t,'el'))
         ;