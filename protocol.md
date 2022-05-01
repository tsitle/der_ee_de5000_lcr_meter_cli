# DER EE DE-5000 LCR Meter Data Protocol

The meter uses the Cyrustek ES51919 chipset which is also used in other LCR meters.  
See [ES51919 protocol description](https://sigrok.org/wiki/Multimeter_ICs/Cyrustek_ES51919) and [ES51919 driver](https://github.com/merbanan/libsigrok/blob/master/src/lcr/es51919.c) in [sigrok project](https://sigrok.org/wiki/Main_Page).

Each packet contains 17 bytes.

```
Byte    Meaning
====    =======
0x00    Header, always 0x00
0x01    Header, always 0x0D

0x02    Flags
        bit 0: hold enabled
        bit 1: reference value shown in delta mode (delta sign is blinking)
        bit 2: delta mode
        bit 3: calibration mode
        bit 4: sorting mode
        bit 5: LCR AUTO mode
        bit 6: auto range mode (is not used in sorting mode only)
        bit 7: parallel measurement (vs. serial)

0x03    Config
        bit 0-4: unknown
        bit 5-7: test frequency
                 0 = 100 Hz
                 1 = 120 Hz
                 2 = 1 kHz
                 3 = 10 kHz
                 4 = 100 kHz
                 5 = 0 Hz (DC)

0x04    Tolerance in sorting mode
        0 = not set
        3 = +-0.25%
        4 = +-0.5%
        5 = +-1%
        6 = +-2%
        7 = +-5%
        8 = +-10%
        9 = +-20%
        10 = -20+80%

Bytes 0x05-0x09 describe primary measurement
0x05    Measured quantity
        1 = inductance
        2 = capacitance
        3 = resistance
        4 = DC resistance

0x06    Measurement MSB  (0x4e20 = 20000 = outside limits)
0x07    Measurement LSB

0x08    Measurement info
        bit 0-2: decimal point multiplier (10^-val)
        bit 3-7: units
                 0 = no unit
                 1 = Ohm
                 2 = kOhm
                 3 = MOhm
                 4 = ?
                 5 = uH
                 6 = mH
                 7 = H
                 8 = kH
                 9 = pF
                 10 = nF
                 11 = uF
                 12 = mF
                 13 = %
                 14 = degree

0x09    Measurement display status
        bit 0-3: Display mode
                 0 = normal (measurement shown)
                 1 = blank (nothing shown)
                 2 = lines ("----")
                 3 = outside limits ("OL")
                 7 = PASS (sorting mode)
                 8 = FAIL (sorting mode)
                 9 = OPEn (calibration mode)
                 10 = Srt (calibration mode)
        bit 4-6: unknown (maybe part of same field with 0-3)
        bit 7:   unknown

Bytes 0x0A-0x0E describe secondary measurement
0x0A    Measured quantity
        0 = none
        1 = D (dissipation factor)
        2 = Q (quality factor)
        3 = ESR/RP (serial/parallel AC resistance)
        4 = Theta (phase angle)

0x0B    Measurement MSB
0x0C    Measurement LSB

0x0D    Measurement info
        bit 0-2: decimal point multiplier (10^-val)
        bit 3-7: units (same as in primary measurement)

0x0E    Measurement display status. Same as byte 0x09 in primary measurement.

0x0F    Footer, always 0x0D
0x10    Footer, always 0x0A
```

Each measurement value is encoded by 3 bytes: two bytes for value (bytes 0x06, 0x07 for primary and 0x0B, 0x0C for secondary) and 3 bits of another byte for multiplier (bytes 0x08 for primary and 0x0D for secondary). The value can be calculated using the following formula:

```(MSB * 0x10000 + LSB) * 10^-multiplier```
