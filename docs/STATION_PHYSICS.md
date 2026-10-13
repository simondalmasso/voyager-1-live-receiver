# Station Physics

Station readiness computes effective aperture, antenna gain, approximate HPBW, G/T, SEFD and radiometer-equation sensitivity only when required inputs exist. System temperature can be supplied directly or estimated from receiver noise figure; the latter is labeled as an equivalent estimate.

Truth states are `STATION_MODEL_INCOMPLETE`, `STATION_MODEL_ESTIMATED`, and `STATION_MODEL_CALIBRATED`. The result is always a `FEASIBILITY_ESTIMATE`; it never says `CAN_RECEIVE_VOYAGER=YES`. Missing parameters and assumptions remain visible.
