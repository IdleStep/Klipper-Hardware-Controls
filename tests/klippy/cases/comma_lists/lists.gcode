; EXHAUST_FAN reaches both fans that exist. The name that matches nothing is skipped.
EXHAUST_FAN SPEED=0.5
ASSERT_FAN FAN=exhaust_fan SPEED=0.5
ASSERT_FAN FAN=external_pc SPEED=0.5
; A string of pin names is split, not read one letter at a time.
LED_ON
ASSERT_VAR MACRO=SET_PIN VARIABLE=value_daystick VALUE=1.0
ASSERT_VAR MACRO=SET_PIN VARIABLE=value_plainstick VALUE=1.0
; The check finds both fans and warns once for missing_fan. The other warnings are th_leds,
; the two steppers that the test printer does not have, and the summary line.
HARDWARE_CHECK
ASSERT_VAR MACRO=RESPOND VARIABLE=warnings VALUE=5
ASSERT_VAR MACRO=RESPOND VARIABLE=errors VALUE=0
