
* ------------------------------------------------------------------------------
* scenario parameters
parameters
         EUA_SCENARIO            scenario emission allowance price
         WIND_ON_LIMIT           upper limit on onshore wind deployment
         FLOW_LIMIT              upper limit on electricity exchange
;

$gdxin medea_%scenario%_data
$load  WIND_ON_LIMIT EUA_SCENARIO FLOW_LIMIT
$gdxin

* ------------------------------------------------------------------------------
* scenario parameters
* ------------------------------------------------------------------------------
PRICE_CO2(t,z) = EUA_SCENARIO;

invest_res.UP('AT','wind_on') = WIND_ON_LIMIT;
invest_res.UP('AT','pv') = 33.5;
invest_thermal.UP('AT','bio') = 0;
invest_thermal.UP('AT','bio_chp') = 0;
invest_thermal.UP('DE','bio') = 1;
invest_thermal.UP('DE','bio_chp') = 1;

flow.UP(z,zz,t) = FLOW_LIMIT;
flow.LO(z,zz,t) = -FLOW_LIMIT;
* no flows from region to itself
flow.FX(z,zz,t)$(not ATC(z,zz))   = 0;
flow.FX(zz,z,t)$(not ATC(zz,z))   = 0;

* ------------------------------------------------------------------------------
* policy constraints
* ------------------------------------------------------------------------------

equations
         policy_100resbalance    policy constraint requiring "100%" renewable electricity generation over year
;
* ------------------------------------------------------------------------------

policy_100resbalance..
         sum((t,tec_itm),
                 GEN_PROFILE('AT',t,tec_itm) * (INSTALLED_CAP_ITM('AT',tec_itm)
                 + invest_res('AT',tec_itm)) )
         + sum(t, q_gen('AT',t,'bio_chp','el'))
         + sum(t, q_gen('AT',t,'bio','el'))
         + sum((t,tec_strg), q_store_out('AT',t,tec_strg))
         - sum((t,tec_strg), q_store_in('AT',t,tec_strg) * STORAGE_PROPERTIES('AT',tec_strg,'efficiency_in'))
         =G=
         0.90 * sum(t, CONSUMPTION('AT',t,'el'))
         ;
