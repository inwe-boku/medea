$title add-on to medea_main.gms to include custom model modifications

* example: modification of CO2 price
* ------------------------------------------------------------------------------

* generate scenario parameter -- same parameter must be included in medea_%scenario%_data.gdx
parameters
         CO2_SCENARIO            scenario emission allowance price
;

* read scenario parameter from scenario .gdx-file
$gdxin medea_%scenario%_data
$load  CO2_SCENARIO
$gdxin

* set model parameter to scenario parameter value
PRICE_CO2(t,r) = CO2_SCENARIO;
