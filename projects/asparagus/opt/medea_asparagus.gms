$title add-on to medea_main.gms to include custom model modifications

* example: modification of CO2 price
* ------------------------------------------------------------------------------

* generate scenario parameter -- same parameter must be included in medea_%scenario%_data.gdx
parameters
         CO2_SCENARIO            scenario emission allowance price
         WIND_ON_LIMIT           upper limit on onshore wind deployment
         FLOW_LIMIT              upper limit on electricity exchange
         PV_CAPEX                annuity of PV capex
         SWITCH_POLICY           switch for policy constraint
;

* read scenario parameter from scenario .gdx-file
$gdxin medea_%scenario%_data
$load  CO2_SCENARIO WIND_ON_LIMIT FLOW_LIMIT PV_CAPEX SWITCH_POLICY
$gdxin

* set model parameter to scenario parameter value
PRICE_CO2(z,t) = CO2_SCENARIO;
CAPITALCOST_R(z,'pv') = PV_CAPEX;

add_r.UP('AT','wind_on') = WIND_ON_LIMIT;
add_r.UP('AT','pv') = 80;
add_r.UP('AT','wind_off') = 0;

add_r.FX('DE','wind_off') = 20 - INITIAL_CAP_R('DE','wind_off');
add_r.FX('DE','wind_on') = 71 - INITIAL_CAP_R('DE','wind_on');
add_r.FX('DE','pv') = 100 - INITIAL_CAP_R('DE','pv');
add_r.UP(z,'ror') = 0;


add_g.UP('AT','bio') = 0;
add_g.UP('AT','bio_chp') = 0;
add_g.FX('DE','bio') = 0;
add_g.FX('DE','bio_chp') = 0;
add_g.UP(z,'nuc') = 0;
add_g.UP(z,'lig_stm') = 0;
add_g.UP(z,'lig_stm_chp') = 0;
add_g.UP(z,'lig_boa') = 0;
add_g.UP(z,'lig_boa_chp') = 0;
add_g.UP(z,'coal_sub') = 0;
add_g.UP(z,'coal_sub_chp') = 0;
add_g.UP(z,'coal_sc') = 0;
add_g.UP(z,'coal_sc_chp') = 0;
add_g.UP(z,'coal_usc') = 0;
add_g.UP(z,'coal_usc_chp') = 0;
add_g.UP(z,'ng_cbt_lo') = 0;
add_g.UP(z,'ng_cbt_lo_chp') = 0;
add_g.UP(z,'ng_cc_lo') = 0;
add_g.UP(z,'ng_cc_lo_chp') = 0;

add_s.UP(z,'hyd_res_day') = 0;
add_s.UP(z,'hyd_res_week') = 0;
add_s.UP(z,'hyd_res_season') = 0;
add_s.UP(z,'hyd_psp_day') = 0;
add_s.UP(z,'hyd_psp_week') = 0;
add_s.UP(z,'hyd_psp_season') = 0;

add_v.UP(z,'hyd_res_day') = 0;
add_v.UP(z,'hyd_res_week') = 0;
add_v.UP(z,'hyd_res_season') = 0;
add_v.UP(z,'hyd_psp_day') = 0;
add_v.UP(z,'hyd_psp_week') = 0;
add_v.UP(z,'hyd_psp_season') = 0;

add_x.UP(z,zz) = FLOW_LIMIT;
*add_x.LO(z,zz,t) = -FLOW_LIMIT;
* no transmission from region to itself
*x.FX(z,zz,t)$(not INITIAL_CAP_X(z,zz)) = 0;
*x.FX(zz,z,t)$(not INITIAL_CAP_X(zz,z)) = 0;
* ------------------------------------------------------------------------------
* policy constraints
* ------------------------------------------------------------------------------

equations
         policy_100resbalance    policy constraint requiring "100%" renewable electricity generation over year
;
* ------------------------------------------------------------------------------
* according to govt need 27 TWh additional energy from RES to meet target
policy_100resbalance$(SWITCH_POLICY)..
         sum((t,n), GEN_PROFILE('AT',t,n) * (INITIAL_CAP_R('AT',n) + add_r('AT',n) ) )
         + sum(t, g('AT',t,'bio_chp','el','biomass'))
         + sum(t, g('AT',t,'bio','el','biomass'))
         + sum((t,k), INFLOWS('AT',t,k)* EFFICIENCY_S_OUT(k))
         =G=
         78291.7
         ;
