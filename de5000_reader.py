"""
CLI Application for reading data from the
  DER EE DE-5000 LCR Meter
via UART

by TS, Apr 2022

based on https://github.com/4x1md/de5000_lcr_py by '4x1md'
"""

from tsitle.der_ee_de5000_lcr_meter_uart.de5000_uart import DE5000Uart
import sys
import time
import datetime
from serial import SerialException

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

PORT = "/dev/ttyUSB0"
SLEEP_TIME = 1.0

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def _pretty_print_meas(data, dispNormVal = False, dispErrRate = False):
	""" Prints measurement details in pretty print

	Parameters:
		data (dict)
		dispNormVal (bool): if True output normalized values
		dispErrRate (bool): if True output transmission error rate
	"""
	if data["data_valid"] == False:
		print(f"DE-5000 is not connected or data was corrupted. (Packets: {data['packCountErr']} invalid, {data['packCountOk']} OK)")
		if data["dbgMsg"]:
			print(f"  -- {data['dbgMsg']}")
		return

	if dispErrRate:
		tmpTotalPacks = data["packCountErr"] + data["packCountOk"]
		tmpErrPerc = (data["packCountErr"] / tmpTotalPacks) * 100.0
		print(f"ErrRate: {data['packCountErr']}/{tmpTotalPacks}={tmpErrPerc:.01f}%")

	# Calibration Mode
	if data["cal_mode"]:
		print("Calibration")
		return

	# Sorting Mode
	if data["sorting_mode"]:
		print("SORTING Tol %s" % data["tolerance"])

	# Test Frequency
	print("Frequency: %s" % data["freq"])

	# LCR Autodetection Mode
	if data["lcr_auto"]:
		print("LCR AUTO")

	# Auto Range
	if data["auto_range"]:
		print("AUTO RNG")

	# Delta Mode Parameters
	if data["delta_mode"]:
		if data["ref_shown"]:
			print("DELTA Ref")
		else:
			print("DELTA")

	# Main Display
	if data["main_status"] and data["main_status"] != "blank":
		print("Primary:   ", end="")
		if data["main_status"] == "normal":
			print(f"{data['main_quantity']:5s} = ", end="")
			if dispNormVal:
				print(f"{data['main_norm_val']:.12f} {data['main_norm_units']}")
			else:
				print(f"{data['main_val']:.04f} {data['main_units']}")
		else:
			print(f"{data['main_status']}")

	# Secondary Display
	if data["sec_status"] and data["sec_status"] != "blank":
		print("Secondary: ", end="")
		if data["sec_status"] == "normal":
			if data["sec_quantity"]:
				print(f"{data['sec_quantity']:5s} = ", end="")
			if dispNormVal:
				print(f"{data['sec_norm_val']:.12f} {data['sec_norm_units']}")
			else:
				print(f"{data['sec_val']:.04f} {data['sec_units']}")
		else:
			print(f"{data['sec_status']}")

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

if __name__ == "__main__":
	try:
		if len(sys.argv) > 1:
			port = sys.argv[1]
		else:
			port = PORT

		print(f"Starting DE-5000 monitor... (port={port})")
		lcr = DE5000Uart(port)

		while True:
			print("")
			print(datetime.datetime.now())
			# @var data: dict
			data = lcr.get_meas()
			_pretty_print_meas(data, dispNormVal=False, dispErrRate=False)

			time.sleep(SLEEP_TIME)
	except SerialException as err:
		print("Serial port error: ", err)
		sys.exit(1)
	except KeyboardInterrupt:
		print("")
		print("Exiting DE-5000 monitor.")
