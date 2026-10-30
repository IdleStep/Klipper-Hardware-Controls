; The test printer has no steppers and no th_leds neopixel, so three roles report a name that
; matches nothing, and the summary is a warning too.
HARDWARE_CHECK
ASSERT_VAR MACRO=RESPOND VARIABLE=warnings VALUE=4
ASSERT_VAR MACRO=RESPOND VARIABLE=errors VALUE=0
