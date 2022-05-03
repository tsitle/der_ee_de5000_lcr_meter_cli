#
# by TS, Apr 2022
#

import calendar
import csv
from os import linesep, path
import sys
from typing import Callable

from tsitle.der_ee_de5000_lcr_meter_uart.de5000_uart import \
		STATUS_NORMAL, STATUS_BLANK, STATUS_OL, STATUS_PASS, STATUS_FAIL, \
		UNIT_NORMALIZED_L, UNIT_NORMALIZED_C, UNIT_NORMALIZED_R, \
		MAIN_QUANTITY_LS, MAIN_QUANTITY_LP, \
		MAIN_QUANTITY_CS, MAIN_QUANTITY_CP, \
		MAIN_QUANTITY_RS, MAIN_QUANTITY_RP, \
		MAIN_QUANTITY_DCR, \
		SEC_QUANTITY_D, SEC_QUANTITY_Q, SEC_QUANTITY_ESR, \
		SEC_QUANTITY_THETA, SEC_QUANTITY_RP, SEC_QUANTITY_DELTA
from tsitle.der_ee_de5000_lcr_meter_uart.de5000_stc_packet import \
		De5000StcPacket, De5000StcPacketMainSecondary

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class OutputCommon(object):
	def __init__(self, debugMsgCb: Callable[[str], None]):
		""" Initialize object

		Parameters:
			debugMsgCb (Callable[[str], None])
		"""
		assert debugMsgCb is not None, "debugMsgCb needs to be function"
		#
		self._debug_msg_cb = debugMsgCb
		#
		self._sortRefVal = None
		self._sortRefUnit = None
		self._deltaRefVal = None
		self._deltaRefUnit = None

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class CsvOutput(OutputCommon):
	_ROW_HD_TS_UTC = "Timestamp UTC"
	_ROW_HD_DT_UTC = "DateTime UTC"
	_ROW_HD_DISP_PREFIX_MAIN = "Main"
	_ROW_HD_DISP_PREFIX_SEC = "Sec"
	_ROW_HD_DISP_SUFFIX_L = f"L [{UNIT_NORMALIZED_L}]"
	_ROW_HD_DISP_SUFFIX_C = f"C [{UNIT_NORMALIZED_C}]"
	_ROW_HD_DISP_SUFFIX_R = f"R [{UNIT_NORMALIZED_R}]"
	_ROW_HD_DISP_SUFFIX_D = "D"
	_ROW_HD_DISP_SUFFIX_Q = "Q"
	_ROW_HD_DISP_SUFFIX_THETA = "Theta [degree]"
	_ROW_HD_DISP_SUFFIX_QUANT = "Quantity"
	_ROW_HD_DISP_SUFFIX_DELTA = "Delta [%]"
	_ROW_HD_DISP_SUFFIX_OL = "Overload [bool]"
	_ROW_HD_FREQ = "Freq [Hz]"
	_ROW_HD_TOL = "Tolerance"
	_ROW_HD_SORT_PASSED = "Sorting Passed [bool]"
	_ROW_HD_SORT_REF = "Sorting Reference"
	_ROW_HD_DELTA_REF = "Delta Reference"
	_ROW_HD_IS_DELTA_MODE = "is Delta Mode [bool]"
	_ROW_HD_IS_SORT_MODE = "is Sorting Mode [bool]"
	_ROW_HD_IS_LCR_AUTO_MODE = "is LCR Auto Mode [bool]"
	_ROW_HD_IS_AUTO_RANGE_MODE = "is Auto Range Mode [bool]"
	#
	_STR_TRUE = "true"
	_STR_FALSE = "false"

	def __init__(self, csvFn: str, debugMsgCb: Callable[[str], None]):
		""" Initialize object

		Parameters:
			csvFn (str)
			debugMsgCb (Callable[[str], None])
		"""
		assert csvFn is not None and isinstance(csvFn, str), "csvFn needs to be string"
		assert csvFn != "", "csvFn needs to be non-empty string"
		#
		super().__init__(debugMsgCb)
		#
		self._fHnd = None
		self._dictWr = None
		self._csvFn = csvFn

	def openCsv(self):
		""" Open CSV file - if the file does not exist it will be created """
		fieldnames = self._get_csv_header()
		#
		fileExisted = path.isfile(self._csvFn)
		self._fHnd = open(self._csvFn, mode="a")
		self._dictWr = csv.DictWriter(self._fHnd, fieldnames=fieldnames, lineterminator=linesep)
		if not fileExisted:
			self._dictWr.writeheader()

	def writeCsvDecodedPacket(self, packet: De5000StcPacket):
		""" Write a decoded packet to CSV file

		Parameters:
			packet (De5000StcPacket)
		Raises:
			Exception
		"""
		if self._fHnd is None or self._dictWr is None:
			raise Exception("need to call createCsv() first")
		#
		if not packet.dataValid:
			return
		if packet.sortingMode and packet.dispMain.status in [STATUS_NORMAL, STATUS_OL] and packet.dispSec.status == STATUS_BLANK:
			# the setup for Component Sorting is being entered into the meter
			#self._debug_msg_cb("(in sorting setup mode) (CSV)")
			self._sortRefVal = packet.dispMain.normVal
			self._sortRefUnit = packet.dispMain.normUnits
			#self._debug_msg_cb(f"setting sortRefVal to {packet.dispMain.normVal:.09f} {packet.dispMain.normUnits} (CSV)")
			return
		elif not packet.sortingMode and self._sortRefVal:
			#self._debug_msg_cb(f"resetting sortRefVal (CSV)")
			self._sortRefVal = None
			self._sortRefUnit = None
		if packet.deltaMode and packet.refShown:
			# the reference value for the Delta Mode is being displayed on the meter
			#self._debug_msg_cb("(showing delta ref value) (CSV)")
			self._deltaRefVal = packet.dispMain.normVal
			self._deltaRefUnit = packet.dispMain.normUnits
			#self._debug_msg_cb(f"setting deltaRefVal to {packet.dispMain.normVal:.09f} {packet.dispMain.normUnits} (CSV)")
			return
		elif not packet.deltaMode and self._deltaRefVal:
			#self._debug_msg_cb(f"resetting deltaRefVal (CSV)")
			self._deltaRefVal = None
			self._deltaRefUnit = None
		if packet.dispMain.status not in [STATUS_NORMAL, STATUS_OL, STATUS_PASS, STATUS_FAIL]:
			# the meter is not displaying anything helpful at the moment
			#self._debug_msg_cb("(main display blank) (CSV)")
			return
		#
		tsSecStr = "{:010d}".format(calendar.timegm(packet.timestamp.timetuple()))
		tsMsStr = "{:06d}".format(packet.timestamp.microsecond)
		rowVals = {
				self._ROW_HD_TS_UTC: "{:s}.{:s}".format(tsSecStr, tsMsStr),  # UTC Timestamp as integer plus microseconds
				self._ROW_HD_DT_UTC: str(packet.timestamp),  # UTC Date/Time
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_QUANT}": "",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_L}": "",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_C}": "",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_R}": "",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_OL}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_QUANT}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_L}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_C}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_R}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_D}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_Q}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_THETA}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_DELTA}": "",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_OL}": "",
				self._ROW_HD_FREQ: "",
				self._ROW_HD_TOL: "",
				self._ROW_HD_SORT_PASSED: "",
				self._ROW_HD_SORT_REF: "",
				self._ROW_HD_DELTA_REF: "",
				self._ROW_HD_IS_DELTA_MODE: "",
				self._ROW_HD_IS_SORT_MODE: "",
				self._ROW_HD_IS_LCR_AUTO_MODE: "",
				self._ROW_HD_IS_AUTO_RANGE_MODE: ""
			}
		#
		rowVals = self._get_csv_cols_display(rowVals, packet.dispMain, self._ROW_HD_DISP_PREFIX_MAIN)
		if packet.dispSec.status in [STATUS_NORMAL, STATUS_OL]:
			rowVals = self._get_csv_cols_display(rowVals, packet.dispSec, self._ROW_HD_DISP_PREFIX_SEC)
		#
		rowVals[self._ROW_HD_FREQ] = packet.freq if packet.freq else ""
		if rowVals[self._ROW_HD_FREQ].endswith(" Hz"):
			rowVals[self._ROW_HD_FREQ] = rowVals[self._ROW_HD_FREQ].replace(" Hz", "")
		elif rowVals[self._ROW_HD_FREQ].endswith(" kHz"):
			rowVals[self._ROW_HD_FREQ] = str(int(rowVals[self._ROW_HD_FREQ].replace(" kHz", "")) * 1000)
		elif rowVals[self._ROW_HD_FREQ] == "DC":
			rowVals[self._ROW_HD_FREQ] = "0"
		rowVals[self._ROW_HD_TOL] = packet.tolerance if packet.tolerance else ""
		if packet.deltaMode:
			if self._deltaRefVal:
				rowVals[self._ROW_HD_DELTA_REF] = f"{self._deltaRefVal} {self._deltaRefUnit}"
			else:
				rowVals[self._ROW_HD_DELTA_REF] = "n/a"
		rowVals[self._ROW_HD_IS_DELTA_MODE] = self._STR_TRUE if packet.deltaMode else self._STR_FALSE
		rowVals[self._ROW_HD_IS_SORT_MODE] = self._STR_TRUE if packet.sortingMode else self._STR_FALSE
		rowVals[self._ROW_HD_IS_LCR_AUTO_MODE] = self._STR_TRUE if packet.lcrAuto else self._STR_FALSE
		rowVals[self._ROW_HD_IS_AUTO_RANGE_MODE] = self._STR_TRUE if packet.autoRange else self._STR_FALSE
		#
		self._dictWr.writerow(rowVals)
		self._fHnd.flush()

	def closeCsv(self):
		""" Close CSV file """
		if self._fHnd is None:
			return
		self._fHnd.close()
		self._fHnd = None

	@property
	def isOpen(self):
		return (self._fHnd is not None)

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _get_csv_header(self) -> list:
		""" Get array with CSV header entries

		Returns:
			list
		"""
		resA = [
				self._ROW_HD_TS_UTC,
				self._ROW_HD_DT_UTC,
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_QUANT}",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_L}",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_C}",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_R}",
				f"{self._ROW_HD_DISP_PREFIX_MAIN} {self._ROW_HD_DISP_SUFFIX_OL}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_QUANT}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_L}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_C}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_R}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_D}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_Q}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_THETA}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_DELTA}",
				f"{self._ROW_HD_DISP_PREFIX_SEC} {self._ROW_HD_DISP_SUFFIX_OL}",
				self._ROW_HD_FREQ,
				self._ROW_HD_TOL,
				self._ROW_HD_SORT_PASSED,
				self._ROW_HD_SORT_REF,
				self._ROW_HD_DELTA_REF,
				self._ROW_HD_IS_DELTA_MODE,
				self._ROW_HD_IS_SORT_MODE,
				self._ROW_HD_IS_LCR_AUTO_MODE,
				self._ROW_HD_IS_AUTO_RANGE_MODE
			]
		return resA

	def _get_csv_cols_display(self, rowVals: dict, packetDisp: De5000StcPacketMainSecondary, colPrefix: str) -> dict:
		if not packetDisp.quantity:
			#self._debug_msg_cb(f"({colPrefix} no quant) (CSV)")
			return rowVals
		rowVals[f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_QUANT}"] = packetDisp.quantity
		rowVals[f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_OL}"] = self._STR_FALSE
		#
		colA = ""
		colB = ""
		if packetDisp.status == STATUS_OL:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_OL}"
		elif packetDisp.status in [STATUS_PASS, STATUS_FAIL]:
			colA = self._ROW_HD_SORT_PASSED
			colB = self._ROW_HD_SORT_REF
		elif packetDisp.quantity in [MAIN_QUANTITY_LS, MAIN_QUANTITY_LP]:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_L}"
		elif packetDisp.quantity in [MAIN_QUANTITY_CS, MAIN_QUANTITY_CP]:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_C}"
		elif packetDisp.quantity in [MAIN_QUANTITY_RS, MAIN_QUANTITY_RP, MAIN_QUANTITY_DCR, SEC_QUANTITY_ESR, SEC_QUANTITY_RP]:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_R}"
		elif packetDisp.quantity == SEC_QUANTITY_D:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_D}"
		elif packetDisp.quantity == SEC_QUANTITY_Q:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_Q}"
		elif packetDisp.quantity == SEC_QUANTITY_THETA:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_THETA}"
		elif packetDisp.quantity == SEC_QUANTITY_DELTA:
			colA = f"{colPrefix} {self._ROW_HD_DISP_SUFFIX_DELTA}"
			colB = self._ROW_HD_DELTA_REF
		#
		if colA:
			#self._debug_msg_cb(f"colA='{colA}', colB='{colB}' (CSV)")
			if packetDisp.status in [STATUS_PASS, STATUS_FAIL]:
				rowVals[colA] = self._STR_TRUE if packetDisp.status == STATUS_PASS else self._STR_FALSE
				if self._sortRefVal:
					rowVals[colB] = f"{self._sortRefVal} {self._sortRefUnit}"
				else:
					rowVals[colB] = "n/a"
				#self._debug_msg_cb(f"valB='{rowVals[colB]}' (CSV)")
			elif packetDisp.status == STATUS_NORMAL:
				rowVals[colA] = f"{packetDisp.normVal:.09f}" if packetDisp.normVal else ""
			else:
				# Status is "Overload"
				rowVals[colA] = self._STR_TRUE
			#self._debug_msg_cb(f"valA='{rowVals[colA]}' (CSV)")
		return rowVals

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class ConsoleOutput(OutputCommon):
	def __init__(self, debugMsgCb: Callable[[str], None], statusMsgCb: Callable[[str], None]):
		""" Initialize object

		Parameters:
			debugMsgCb (Callable[[str], None])
			statusMsgCb (Callable[[str], None])
		"""
		assert statusMsgCb is not None, "statusMsgCb needs to be function"
		#
		super().__init__(debugMsgCb)
		#
		self._status_msg_cb = statusMsgCb

	def print_decoded_packet(self, packet: De5000StcPacket, dispNormVal = False, dispErrorRate = False):
		""" Print a decoded packet to screen

		Parameters:
			packet (De5000StcPacket)
			dispNormVal (bool): if True output normalized values
			dispErrorRate (bool): if True output transmission error rate
		"""
		if not packet.dataValid:
			return

		#
		self._status_msg_cb(packet.timestamp)

		# Transmission Error Rate
		if dispErrorRate:
			tmpTotalPacks = packet.packetCountErr + packet.packetCountOk
			tmpErrPerc = (packet.packetCountErr / tmpTotalPacks) * 100.0
			self._status_msg_cb(f"ErrRate: {packet.packetCountErr}/{tmpTotalPacks}={tmpErrPerc:.01f}%")

		# Calibration Mode
		if packet.calMode:
			self._status_msg_cb("Calibration")
			return

		# Sorting Mode
		if packet.sortingMode:
			self._status_msg_cb("SORTING Tol %s" % packet.tolerance)

		# Test Frequency
		self._status_msg_cb("Frequency: %s" % packet.freq)

		# LCR Autodetection Mode
		if packet.lcrAuto:
			self._status_msg_cb("LCR AUTO")

		# Auto Range
		if packet.autoRange:
			self._status_msg_cb("AUTO RNG")

		# Delta Mode Parameters
		if packet.deltaMode:
			if packet.refShown:
				self._status_msg_cb("DELTA (showing reference)")
				# the reference value for the Delta Mode is being displayed on the meter
				self._deltaRefVal = packet.dispMain.normVal
				self._deltaRefUnit = packet.dispMain.normUnits
				#self._debug_msg_cb(f"setting deltaRefVal to {packet.dispMain.normVal:.09f} {packet.dispMain.normUnits} (CON)")
			else:
				self._status_msg_cb("DELTA")

		# Main + Secondary Display
		if packet.sortingMode and packet.dispMain.status in [STATUS_NORMAL, STATUS_OL] and packet.dispSec.status == STATUS_BLANK:
			# the setup for Component Sorting is being entered into the meter
			self._status_msg_cb("(in sorting setup mode)")
			self._sortRefVal = packet.dispMain.normVal
			self._sortRefUnit = packet.dispMain.normUnits
			self._status_msg_cb(f"(setting sorting reference to {packet.dispMain.normVal:.09f} {packet.dispMain.normUnits})")
		else:
			self._print_decoded_packet_display("Primary", packet.dispMain, dispNormVal=dispNormVal)
			self._print_decoded_packet_display("Secondary", packet.dispSec, dispNormVal=dispNormVal)

		# Sorting Reference
		if packet.sortingMode and packet.dispMain.status in [STATUS_PASS, STATUS_FAIL]:
			msg = "Sorting Reference: "
			if self._sortRefVal:
				msg += f"{self._sortRefVal} {self._sortRefUnit}"
			else:
				msg += "n/a"
			self._status_msg_cb(msg)
		elif not packet.sortingMode and self._sortRefVal:
			#self._debug_msg_cb(f"resetting sortRefVal (CON)")
			self._sortRefVal = None
			self._sortRefUnit = None

		# Delta Reference
		if packet.deltaMode and not packet.refShown:
			msg = "Delta Reference: "
			if self._deltaRefVal:
				msg += f"{self._deltaRefVal} {self._deltaRefUnit}"
			else:
				msg += "n/a"
			self._status_msg_cb(msg)
		elif not packet.deltaMode and self._deltaRefVal:
			#self._debug_msg_cb(f"resetting deltaRefVal (CON)")
			self._deltaRefVal = None
			self._deltaRefUnit = None

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _print_decoded_packet_display(self, desc: str, packetDisp: De5000StcPacketMainSecondary, dispNormVal = False):
		#self._debug_msg_cb(str(packetDisp) + " (CON)")
		#
		if not packetDisp.status or packetDisp.status == STATUS_BLANK:
			return
		msg = f"{desc:9s}: "
		if packetDisp.status in [STATUS_NORMAL, STATUS_OL, STATUS_PASS, STATUS_FAIL]:
			if packetDisp.quantity:
				msg += f"{packetDisp.quantity:5s} = "
			else:
				msg += "n/a = "
			if packetDisp.status == STATUS_NORMAL:
				if dispNormVal:
					msg += f"{packetDisp.normVal:.09f} {packetDisp.normUnits}"
				else:
					msg += f"{packetDisp.val:.04f} {packetDisp.units}"
			else:
				msg += f"{packetDisp.status}"
		else:
			msg += f"{packetDisp.status}"
		self._status_msg_cb(msg)
