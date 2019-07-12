
* ------------------------------------------------------------------------------
* scenario parameters
parameters
         EUA_SCENARIO            scenario emission allowance price
;

$gdxin medea_%scenario%_data
$load  EUA_SCENARIO
$gdxin

PRICE_EUA(t,r) = EUA_SCENARIO;
