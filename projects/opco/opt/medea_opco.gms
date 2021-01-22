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


* -----------------------------------------------------
* lower limit on renewable electricity generation share
* -----------------------------------------------------
equations
lolim_reshare   lower limit on renewable electricity generation,
uplim_windon    upper limit on deployable wind power
;

lolim_reshare..
         (sum((z,t,n), GEN_PROFILE(z,t,n) * (INITIAL_CAP_R(z,n) + add_r(z,n) ) )
         + sum((z,t), g(z,t,'bio_chp','el','biomass'))
         + sum((z,t), g(z,t,'bio','el','biomass'))
         + sum((z,t,k), INFLOWS(z,t,k)* EFFICIENCY_S_OUT(k)) )
         / sum((z,t), DEMAND(z,t,'el'))
         =G=
         RE_SHARE
         ;

uplim_windon..
        sum(z, add_r(z,'wind_on'))
        =L=
        WIND_ON_LIMIT
        ;

