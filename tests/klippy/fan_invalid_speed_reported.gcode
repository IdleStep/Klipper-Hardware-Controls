EXHAUST_FAN SPEED=0.5
EXTERNAL_PC SPEED=1
BED_FANS SPEED=0.4
; An invalid speed is reported and leaves the fan as it is.
EXHAUST_FAN SPEED=2
EXTERNAL_PC SPEED=abc
BED_FANS SPEED=-0.1
EXHAUST_FAN SPEED=nan
ASSERT_FAN FAN=exhaust_fan SPEED=0.5
ASSERT_FAN FAN=external_pc SPEED=1
ASSERT_FAN FAN=bed_fans SPEED=0.4
; The bad values above must not stop the script.
EXHAUST_FAN SPEED=0.75
ASSERT_FAN FAN=exhaust_fan SPEED=0.75
RESET_FANS
