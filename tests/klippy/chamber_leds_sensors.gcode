CHAMBER TEMP=40
ASSERT_HEATER HEATER=heater_generic:chamber TARGET=40
CHAMBER TEMP=0
ASSERT_HEATER HEATER=heater_generic:chamber TARGET=0
CHAMBER TEMP=40
; An invalid temperature is reported and turns the heater off without an error.
CHAMBER TEMP=abc
ASSERT_HEATER HEATER=heater_generic:chamber TARGET=0
CHAMBER TEMP=40
CHAMBER TEMP=nan
ASSERT_HEATER HEATER=heater_generic:chamber TARGET=0
; An invalid sensor value is reported and leaves the sensor alone.
MOTION_SENSOR ENABLE=abc
SWITCH_SENSOR ENABLE=nan
ASSERT_STATUS OBJECT=filament_motion_sensor:motion_sensor FIELD=enabled VALUE=True
ASSERT_STATUS OBJECT=filament_switch_sensor:switch_sensor FIELD=enabled VALUE=True
MOTION_SENSOR ENABLE=0
SWITCH_SENSOR ENABLE=0
ASSERT_STATUS OBJECT=filament_motion_sensor:motion_sensor FIELD=enabled VALUE=False
ASSERT_STATUS OBJECT=filament_switch_sensor:switch_sensor FIELD=enabled VALUE=False
MOTION_SENSOR ENABLE=1
SWITCH_SENSOR ENABLE=1
ASSERT_STATUS OBJECT=filament_motion_sensor:motion_sensor FIELD=enabled VALUE=True
ASSERT_STATUS OBJECT=filament_switch_sensor:switch_sensor FIELD=enabled VALUE=True
UPDATE_DELAYED_GCODE ID=ENABLE_MOTION_SENSOR DURATION=60
RELEASE_XY
HOTEND_FAN_CHECK
ASSERT_VAR MACRO=_HOTEND_FAN_STATE VARIABLE=stops VALUE=0
ASSERT_VAR MACRO=_HOTEND_FAN_STATE VARIABLE=warned VALUE=True
