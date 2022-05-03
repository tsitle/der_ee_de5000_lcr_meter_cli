#!/usr/bin/env python3

"""
CLI Application for reading data from the
  DER EE DE-5000 LCR Meter
via UART

by TS, Apr 2022

based on https://github.com/4x1md/de5000_lcr_py by '4x1md'
"""

import argparse
import sys
import time
import datetime
from serial import SerialException

import cli_output
from tsitle.der_ee_de5000_lcr_meter_uart.de5000_uart import De5000Uart

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

OPT_MAX_PACKETS_DEF = 0  # 0 means infinite

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class CliDe5000(object):
	_SLEEP_TIME = 1.0

	def __init__(self):
		self._cmdArgs = self._get_parsed_args()
		self._storeCsvFn = ("" if self._cmdArgs["csv"] is None else self._cmdArgs["csv"])
		self._csvOutpObj = (None if self._storeCsvFn == "" else cli_output.CsvOutput(self._storeCsvFn, self._debug_msg_cb))
		self._consoleOutpObj = cli_output.ConsoleOutput(self._debug_msg_cb, self._status_msg_cb)

	def read_from_device(self):
		try:
			port = self._cmdArgs["COM_PORT"]
			dispErrorRate = self._cmdArgs["show_error_rate"]
			#
			if self._csvOutpObj is not None and not self._csvOutpObj.isOpen:
				self._csvOutpObj.openCsv()
			#
			self._status_msg_cb(f"Starting DE-5000 monitor... (port='{port}')")
			lcr = De5000Uart(port)
			#
			while True:
				self._status_msg_cb("")
				# @var packet: De5000StcPacket
				packet = lcr.get_meas()
				#
				if not packet.dataValid:
					self._error_msg_cb("DE-5000 is not connected or data was corrupted. " +
							f"(Packets: {packet.packetCountErr} invalid, {packet.packetCountOk} OK)")
					if packet.dbgMsg:
						self._error_msg_cb(f"  -- {packet.dbgMsg}")
				else:
					self._consoleOutpObj.print_decoded_packet(packet, dispNormVal=True, dispErrorRate=dispErrorRate)
					if self._csvOutpObj is not None and not packet.calMode:
						self._csvOutpObj.writeCsvDecodedPacket(packet)
					if self._cmdArgs["max_packets"] > 0 and packet.packetCountOk >= self._cmdArgs["max_packets"]:
						self._status_msg_cb("")
						self._status_msg_cb("Max packets reached. Stopping...")
						break
				#
				time.sleep(self._SLEEP_TIME)
		except SerialException as err:
			self._error_msg_cb(f"Serial port error: {str(err)}")
			sys.exit(1)
		except KeyboardInterrupt:
			self._status_msg_cb("KeyboardInterrupt.")
		finally:
			if self._csvOutpObj is not None:
				self._csvOutpObj.closeCsv()

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _get_parsed_args(self):
		parser = argparse.ArgumentParser(
				formatter_class=argparse.RawDescriptionHelpFormatter,
				description="Connect to device and continuously print readings",
				epilog=""
			)
		parser.add_argument(
				"--max-packets",
				type=int,
				default=OPT_MAX_PACKETS_DEF,
				help="Maximum amount of packets to receive (default=%d, 0 means infinite)" % OPT_MAX_PACKETS_DEF
			)
		parser.add_argument(
				"--show-error-rate",
				action='store_true',
				help="Enable output of transmission error rate"
			)
		parser.add_argument(
				"--csv",
				help="Output data to CSV file"
			)
		parser.add_argument(
				"COM_PORT",
				help="E.g. '/dev/ttyUSB0'"
			)
		#
		args = parser.parse_args()
		args = vars(args)  # convert into dict
		#
		if args["max_packets"] < 0:
			self._error_msg_cb("! Invalid value for --max-packets (min=0)")
			sys.exit(1)
		#
		if args["csv"] is not None and not args["csv"].endswith(".csv"):
			args["csv"] += ".csv"
		return args

	def _status_msg_cb(self, msg):
		print(msg)

	def _error_msg_cb(self, msg):
		print(msg, file=sys.stderr)

	def _debug_msg_cb(self, msg):
		print(f"-- {msg}")

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

if __name__ == "__main__":
	cliObj = CliDe5000()
	cliObj.read_from_device()
