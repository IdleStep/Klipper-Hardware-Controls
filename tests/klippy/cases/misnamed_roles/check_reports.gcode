; Nothing is wrong with the printer: the chamber, the fans and the LED pins are found. The
; warnings are th_leds and the two steppers, which the test printer does not have, and the
; three mistakes in this case's includes.txt, and the summary line.
HARDWARE_CHECK
ASSERT_VAR MACRO=RESPOND VARIABLE=warnings VALUE=7
ASSERT_VAR MACRO=RESPOND VARIABLE=errors VALUE=0
