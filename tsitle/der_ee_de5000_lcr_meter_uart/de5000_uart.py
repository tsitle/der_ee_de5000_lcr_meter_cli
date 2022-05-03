"""
Driver for reading data from the
  DER EE DE-5000 LCR Meter
via UART

by TS, Apr 2022

based on https://github.com/4x1md/de5000_lcr_py by '4x1md'
"""

import serial

from .de5000_stc_packet import De5000StcPacket

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

STATUS_NORMAL = "normal"
STATUS_BLANK = "blank"
STATUS_OL = "OL"
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"

MAIN_QUANTITY_LS = "Ls"
MAIN_QUANTITY_LP = "Lp"
MAIN_QUANTITY_CS = "Cs"
MAIN_QUANTITY_CP = "Cp"
MAIN_QUANTITY_RS = "Rs"
MAIN_QUANTITY_RP = "Rp"
MAIN_QUANTITY_DCR = "DCR"
SEC_QUANTITY_D = "D"
SEC_QUANTITY_Q = "Q"
SEC_QUANTITY_ESR = "ESR"
SEC_QUANTITY_THETA = "Theta"
SEC_QUANTITY_RP = MAIN_QUANTITY_RP
SEC_QUANTITY_DELTA = "Delta"

UNIT_NORMALIZED_L = "uH"
UNIT_NORMALIZED_C = "uF"
UNIT_NORMALIZED_R = "Ohm"

# ------------------------------------------------------------------------------

# Settings constants (Serial port settings: 9600 8N1 DTR=1 RTS=0)
_BAUD_RATE = 9600
_BITS = serial.EIGHTBITS
_PARITY = serial.PARITY_NONE
_STOP_BITS = serial.STOPBITS_ONE
_TIMEOUT = 1
# Data packet ends with CR LF (\r \n) characters
_DATA_EOL = b"\x0D\x0A"
_RAW_DATA_LENGTH = 17
_READ_RETRIES = 3

# Cyrustek ES51919 protocol constants
# Byte 0x02: flags
# bit 0 = hold enabled
_HOLD = 0b00000001
# bit 1 = reference shown (in delta mode)
_REF_SHOWN = 0b00000010
# bit 2 = delta mode
_DELTA_MODE = 0b00000100
# bit 3 = calibration mode
_CAL_MODE = 0b00001000
# bit 4 = sorting mode
_SORTING_MODE = 0b00010000
# bit 5 = LCR mode
_LCR_AUTO_MODE = 0b00100000
# bit 6 = auto mode
_AUTO_RANGE_MODE = 0b01000000
# bit 7 = parallel measurement (vs. serial)
_PARALLEL = 0b10000000

# Byte 0x03 bits 5-7: Frequency
_FREQ_ARR = [
		"100 Hz",
		"120 Hz",
		"1 KHz",
		"10 KHz",
		"100 KHz",
		"DC"
	]

# Byte 0x04: tolerance
_TOLERANCE_ARR = [
		None,
		None,
		None,
		"+-0.25%",
		"+-0.5%",
		"+-1%",
		"+-2%",
		"+-5%",
		"+-10%",
		"+-20%",
		"-20+80%"
	]

# Byte 0x05: primary measured quantity (serial and parallel mode)
_MAIN_QUANTITY_SER_ARR = [None, MAIN_QUANTITY_LS, MAIN_QUANTITY_CS, MAIN_QUANTITY_RS, MAIN_QUANTITY_DCR]
_MAIN_QUANTITY_PAR_ARR = [None, MAIN_QUANTITY_LP, MAIN_QUANTITY_CP, MAIN_QUANTITY_RP, MAIN_QUANTITY_DCR]

# Bytes 0x08, 0x0D bits 3-7: Units
_MAIN_UNITS_ARR = [
		"",
		"Ohm",
		"kOhm",
		"MOhm",
		None,
		"uH",
		"mH",
		"H",
		"kH",
		"pF",
		"nF",
		"uF",
		"mF",
		"%",
		"deg",
		None, None, None, None, None, None
	]

# Bytes 0x09, 0x0E bits 0-3: Measurement display status
_STATUS_ARR = [
		STATUS_NORMAL,
		STATUS_BLANK,
		"----",
		STATUS_OL,
		None,
		None,
		None,
		STATUS_PASS,
		STATUS_FAIL,
		"OPEn",
		"Srt"
	]

# Byte 0x0a: secondary measured quantity
_SEC_QUANTITY_ARR = [
		None,
		SEC_QUANTITY_D,
		SEC_QUANTITY_Q,
		SEC_QUANTITY_ESR,
		SEC_QUANTITY_THETA
	]

# Normalization constants
# Each value contains multiplier and target value
_NORMALIZE_RULES = {
		"":     (1, ""),
		"Ohm":  (1, UNIT_NORMALIZED_R),
		"kOhm": (1E3, UNIT_NORMALIZED_R),
		"MOhm": (1E6, UNIT_NORMALIZED_R),
		"uH":   (1, UNIT_NORMALIZED_L),
		"mH":   (1E3, UNIT_NORMALIZED_L),
		"H":    (1E6, UNIT_NORMALIZED_L),
		"kH":   (1E9, UNIT_NORMALIZED_L),
		"pF":   (1E-6, UNIT_NORMALIZED_C),
		"nF":   (1E-3, UNIT_NORMALIZED_C),
		"uF":   (1, UNIT_NORMALIZED_C),
		"mF":   (1E3, UNIT_NORMALIZED_C),
		"%":    (1, "%"),
		"deg":  (1, "deg")
	}

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class De5000Uart(object):
	def __init__(self, port):
		""" Initialize object

		Parameters:
			port (str): E.g. '/dev/ttyUSB0'
		"""
		self._port = port
		self._ser = serial.Serial(self._port, _BAUD_RATE, _BITS, _PARITY, _STOP_BITS, timeout=_TIMEOUT)
		self._ser.setDTR(True)
		self._ser.setRTS(False)
		self._ser.close()
		self._ser.open()
		self._packCountOk = 0
		self._packCountErr = 0
		self._lastDbgMsg = ""

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def get_meas(self) -> De5000StcPacket:
		""" Get received measurement as dictionary

		Returns:
			De5000StcPacket
		"""
		if self._ser.isOpen():
			raw_data = self._read_raw_data()
		else:
			raw_data = []

		#
		res = De5000StcPacket()
		res.packetCountOk = self._packCountOk
		res.packetCountErr = self._packCountErr
		res.dbgMsg = self._lastDbgMsg

		# If raw data is empty, return
		if len(raw_data) == 0:
			self._packCountErr += 1
			res.packetCountErr += 1
			return res
		self._packCountOk += 1
		res.packetCountOk += 1

		# Frequency
		val = raw_data[0x03]
		val &= 0b11100000
		val = val >> 5
		res.freq = _FREQ_ARR[val].replace("KHz", "kHz")

		# Reference shown
		val = raw_data[0x02]
		val &= _REF_SHOWN
		res.refShown = True if val else False

		# Delta mode
		val = raw_data[0x02]
		val &= _DELTA_MODE
		res.deltaMode = True if val else False

		# Calibration mode
		val = raw_data[0x02]
		val &= _CAL_MODE
		res.calMode = True if val else False

		# Sorting mode
		val = raw_data[0x02]
		val &= _SORTING_MODE
		res.sortingMode = True if val else False

		# LCR AUTO mode
		val = raw_data[0x02]
		val &= _LCR_AUTO_MODE
		res.lcrAuto = True if val else False

		# Auto range
		val = raw_data[0x02]
		val &= _AUTO_RANGE_MODE
		res.autoRange = True if val else False

		# Parallel measurement
		val = raw_data[0x02]
		val &= _PARALLEL
		res.parallel = True if val else False

		# Main measurement
		## Status
		val = raw_data[0x09]
		val &= 0b00001111
		res.dispMain.status = _STATUS_ARR[val]

		## Quantity
		val = raw_data[0x05]
		if res.parallel:
			res.dispMain.quantity = _MAIN_QUANTITY_PAR_ARR[val]
		else:
			res.dispMain.quantity = _MAIN_QUANTITY_SER_ARR[val]

		## Value
		val = raw_data[0x06] * 0x100 + raw_data[0x07]
		mul = raw_data[0x08]
		mul &= 0b00000111
		val = val * 10**-mul
		res.dispMain.val = float(val)

		## Units
		val = raw_data[0x08]
		val &= 0b11111000
		val = val >> 3
		res.dispMain.units = _MAIN_UNITS_ARR[val]

		## Normalize value
		nval = self._normalize_val(res.dispMain.val, res.dispMain.units)
		res.dispMain.normVal = nval[0]
		res.dispMain.normUnits = nval[1]

		# Secondary measurement
		## Status
		val = raw_data[0x0E]
		val &= 0b00000111
		res.dispSec.status = _STATUS_ARR[val]

		## Quantity
		if res.sortingMode:
			res.dispSec.quantity = res.dispMain.quantity
		elif res.deltaMode:
			res.dispSec.quantity = SEC_QUANTITY_DELTA
		else:
			val = raw_data[0x0A]
			if res.parallel and val == 0x03:
				res.dispSec.quantity = SEC_QUANTITY_RP
			else:
				res.dispSec.quantity = _SEC_QUANTITY_ARR[val]

		## Units
		val = raw_data[0x0D]
		val &= 0b11111000
		val = val >> 3
		res.dispSec.units = _MAIN_UNITS_ARR[val]

		## Value
		val = raw_data[0x0B] * 0x100 + raw_data[0x0C]
		""" If units are % or deg, the value may be negative which is
		represented in two's complement form.
		In this case if the highest bit is 1, the value should be converted
		to negative bu substracting it from 0x10000. """
		if res.dispSec.units in ["%", "deg"] and val & 0x1000:
			val = val - 0x10000
		mul = raw_data[0x0D]
		mul &= 0b00000111
		val = val * 10**-mul
		res.dispSec.val = float(val)

		## Normalize value
		nval = self._normalize_val(res.dispSec.val, res.dispSec.units)
		res.dispSec.normVal = nval[0]
		res.dispSec.normUnits = nval[1]

		# Tolerance
		val = raw_data[0x04]
		res.tolerance = _TOLERANCE_ARR[val]

		res.dataValid = True

		return res

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _read_raw_data(self):
		""" Reads a new data packet from serial port.
		If the packet was valid returns array of integers.
		if the packet was not valid returns empty array.

		In order to get the last reading the input buffer is flushed
		before reading any data.

		If the first received packet contains less than 17 bytes, it is
		not complete and the reading is done again. Maximum number of
		retries is defined by _READ_RETRIES value.

		Returns:
			list: List of bytes
		"""
		self._ser.reset_input_buffer()

		retries = 0
		while retries < _READ_RETRIES:
			# @var raw_data: bytes
			raw_data = self._ser.read_until(_DATA_EOL, _RAW_DATA_LENGTH)
			# If 17 bytes were read, the packet is valid and the loop ends.
			if len(raw_data) == _RAW_DATA_LENGTH:
				break
			retries += 1
		res = []
		# Check data validity
		if self._is_data_valid(raw_data):
			res = [c for c in raw_data]
		return res

	def _is_data_valid(self, raw_data):
		""" Checks data validity:
			- 17 bytes long
			- Header bytes 0x00 0x0D
			- Footer bytes 0x0D 0x0A

		Parameters:
			raw_data (bytes)
		Returns:
			bool
		"""
		self._lastDbgMsg = ""
		# Data length
		tmpSz = len(raw_data)
		if tmpSz != _RAW_DATA_LENGTH:
			if tmpSz == 0:
				self._lastDbgMsg = "no data received"
			else:
				self._lastDbgMsg = f"len invalid: {tmpSz} != {_RAW_DATA_LENGTH}"
			return False

		# Start bits
		tmpB1 = 0x00
		tmpB2 = 0x0D
		if raw_data[0] != tmpB1 or raw_data[1] != tmpB2:
			self._lastDbgMsg = f"start bits invalid: {raw_data[0]:02X} != {tmpB1:02X} or {raw_data[1]:02X} != {tmpB2:02X}"
			return False

		# End bits
		tmpB1 = 0x0D
		tmpB2 = 0x0A
		if raw_data[15] != tmpB1 or raw_data[16] != tmpB2:
			self._lastDbgMsg = f"end bits invalid: {raw_data[15]:02X} != {tmpB1:02X} or {raw_data[16]:02X} != {tmpB2:02X}"
			return False

		return True

	def _normalize_val(self, val, units):
		""" Normalizes measured value to standard units. Resistance
		is normalized to Ohm, capacitance to Farad and inductance
		to Henry. Other units are not changed.

		Parameters:
			val (float)
			units (str)
		Returns:
			tuple
		"""
		val = val * _NORMALIZE_RULES[units][0]
		units = _NORMALIZE_RULES[units][1]
		return (val, units)

	def __del__(self):
		if hasattr(self, "_ser"):
			self._ser.close()

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

if __name__ == "__main__":
	pass
