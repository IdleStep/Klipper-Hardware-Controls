; Klipper merges the repeated sections, so the commands still work.
EXHAUST_FAN SPEED=0.5
ASSERT_FAN FAN=exhaust_fan SPEED=0.5
PART_COOLING SPEED=0.25
ASSERT_FAN FAN=part SPEED=0.25
RESET_FANS
ASSERT_FAN FAN=exhaust_fan SPEED=0
