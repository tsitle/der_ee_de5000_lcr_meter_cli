"""
Created on Sep 15, 2017

@author: 4x1md
"""

from de5000 import DE5000
import sys
import time
import datetime
from serial import SerialException


PORT = "/dev/ttyUSB0"
SLEEP_TIME = 1.0


if __name__ == "__main__":
	try:
		if len(sys.argv) > 1:
			port = sys.argv[1]
		else:
			port = PORT

		print(f"Starting DE-5000 monitor... (port={port})")
		lcr = DE5000(port)

		while True:
			print("")
			print(datetime.datetime.now())
			lcr.pretty_print(disp_norm_val=False)

			time.sleep(SLEEP_TIME)
	except SerialException as err:
		print("Serial port error: ", err)
		sys.exit(1)
	except KeyboardInterrupt:
		print("")
		print("Exiting DE-5000 monitor.")
