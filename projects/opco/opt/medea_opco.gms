$title add-on to medea_main.gms to include custom model modifications

* example: modification of CO2 price
* ------------------------------------------------------------------------------

* generate scenario parameter -- same parameter must be included in medea_%scenario%_data.gdx
parameters
         RE_SHARE            scenario renewables share
         WIND_ON_LIMIT       limit on deployable onshore wind power
;

* read scenario parameter from scenario .gdx-file
$gdxin medea_%scenario%_data
$load  RE_SHARE WIND_ON_LIMIT
$gdxin


add_r.UP('AT','wind_off') = 0;
add_r.UP('DE','wind_off') = 25;
add_r.UP(z,'ror') = 0;

add_g.UP('AT','bio') = 0;
add_g.UP('AT','bio_chp') = 0;
add_g.UP('DE','bio') = 1;
add_g.UP('DE','bio_chp') = 1;
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


* -----------------------------------------------------
* lower limit on renewable electricity generation share
* -----------------------------------------------------
equations
lolim_reshare   lower limit on renewable electricity generation,
uplim_windon    upper limit on deployable wind power
;

lolim_reshare..
         (sum((z,t,n), r(z,t,n))
         + sum((z,t), g(z,t,'bio_chp','el','biomass'))
         + sum((z,t), g(z,t,'bio','el','biomass'))
         + sum((z,t,k), INFLOWS(z,t,k)* EFFICIENCY_S_OUT(k)) )
         / sum((z,t), DEMAND(z,t,'el'))
         =G=
         RE_SHARE / 100
         ;

uplim_windon..
        sum(z, add_r(z,'wind_on'))
        =L=
        WIND_ON_LIMIT
        ;

