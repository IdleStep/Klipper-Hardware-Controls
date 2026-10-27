EXHAUST_FAN SPEED=0.5
EXTERNAL_PC SPEED=1
BED_FANS SPEED=0.4
M400
; An invalid speed is reported and leaves the fan as it is.
EXHAUST_FAN SPEED=2
EXTERNAL_PC SPEED=abc
BED_FANS SPEED=-0.1
EXHAUST_FAN SPEED=nan
M400
ASSERT_STATUS OBJECT=fan_generic:exhaust_fan FIELD=speed VALUE=0.5
ASSERT_STATUS OBJECT=fan_generic:external_pc FIELD=speed VALUE=1
ASSERT_STATUS OBJECT=fan_generic:bed_fans FIELD=speed VALUE=0.4
; The bad values above must not stop the script.
EXHAUST_FAN SPEED=0.75
M400
ASSERT_STATUS OBJECT=fan_generic:exhaust_fan FIELD=speed VALUE=0.75
RESET_FANS
