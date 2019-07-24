
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
PRICE_EUA(t,r) = EUA_SCENARIO;

invest_res.UP('AT','wind_on') =  WIND_ON_LIMIT;
invest_res.UP('AT','pv') = 32.5;

flow.UP(r,rr,t) = FLOW_LIMIT;
flow.LO(r,rr,t) = -FLOW_LIMIT;
* no flows from region to itself
flow.FX(r,rr,t)$(not NTC(r,rr))   = 0;
flow.FX(rr,r,t)$(not NTC(rr,r))   = 0;

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
         + sum((t,tec_strg), q_store_out('AT',t,tec_strg))
         - sum((t,tec_strg), q_store_in('AT',t,tec_strg) * STORAGE_PROPERTIES('AT',tec_strg,'efficiency_in'))
         =G=
         0.90 * sum(t, CONSUMPTION('AT',t,'power'))
         ;
