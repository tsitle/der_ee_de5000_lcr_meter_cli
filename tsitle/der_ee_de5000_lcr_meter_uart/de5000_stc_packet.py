#
# by TS, Mai 2022
#

from datetime import datetime
from typing import Optional

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class De5000StcPacketMainSecondary(object):
	def __init__(self):
		self.__quantity = None
		self.__val = None
		self.__units = None
		self.__status = None
		self.__normVal = None
		self.__normUnits = None

	def __str__(self) -> str:
		return f"QU:{self.quantity}, VA:{self.val}, UN:{self.units}, ST:{self.status}"

	@property
	def quantity(self) -> Optional[str]:
		return self.__quantity
	@quantity.setter
	def quantity(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__quantity = value

	@property
	def val(self) -> Optional[float]:
		return self.__val
	@val.setter
	def val(self, value: Optional[float]):
		assert value is None or isinstance(value, float), "value needs to be None or float"
		#
		self.__val = value

	@property
	def units(self) -> Optional[str]:
		return self.__units
	@units.setter
	def units(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__units = value

	@property
	def status(self) -> Optional[str]:
		return self.__status
	@status.setter
	def status(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__status = value

	@property
	def normVal(self) -> Optional[float]:
		return self.__normVal
	@normVal.setter
	def normVal(self, value: Optional[float]):
		assert value is None or isinstance(value, float), "value needs to be None or float"
		#
		self.__normVal = value

	@property
	def normUnits(self) -> Optional[str]:
		return self.__normUnits
	@normUnits.setter
	def normUnits(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__normUnits = value

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class De5000StcPacket(object):
	def __init__(self, timestamp=None):
		assert timestamp is None or isinstance(timestamp, datetime), "timestamp needs to be None or instance of datetime"
		#
		self.__timestamp = timestamp if timestamp is not None else datetime.now()
		#
		self.__dispMain = De5000StcPacketMainSecondary()
		self.__dispSec = De5000StcPacketMainSecondary()
		#
		self.__freq = None
		self.__tolerance = None
		self.__refShown = False
		self.__deltaMode = False
		self.__calMode = False
		self.__sortingMode = False
		self.__lcrAuto = False
		self.__autoRange = False
		self.__parallel = False
		#
		self.__dataValid = False
		self.__packetCountOk = 0
		self.__packetCountErr = 0
		self.__dbgMsg = ""

	@property
	def timestamp(self) -> datetime:
		return self.__timestamp

	@property
	def dispMain(self) -> De5000StcPacketMainSecondary:
		return self.__dispMain

	@property
	def dispSec(self) -> De5000StcPacketMainSecondary:
		return self.__dispSec

	@property
	def freq(self) -> Optional[str]:
		return self.__freq
	@freq.setter
	def freq(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__freq = value

	@property
	def tolerance(self) -> Optional[str]:
		return self.__tolerance
	@tolerance.setter
	def tolerance(self, value: Optional[str]):
		assert value is None or isinstance(value, str), "value needs to be None or string"
		#
		self.__tolerance = value

	@property
	def refShown(self) -> bool:
		return self.__refShown
	@refShown.setter
	def refShown(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__refShown = value

	@property
	def deltaMode(self) -> bool:
		return self.__deltaMode
	@deltaMode.setter
	def deltaMode(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__deltaMode = value

	@property
	def calMode(self) -> bool:
		return self.__calMode
	@calMode.setter
	def calMode(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__calMode = value

	@property
	def sortingMode(self) -> bool:
		return self.__sortingMode
	@sortingMode.setter
	def sortingMode(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__sortingMode = value

	@property
	def lcrAuto(self) -> bool:
		return self.__lcrAuto
	@lcrAuto.setter
	def lcrAuto(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__lcrAuto = value

	@property
	def autoRange(self) -> bool:
		return self.__autoRange
	@autoRange.setter
	def autoRange(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__autoRange = value

	@property
	def parallel(self) -> bool:
		return self.__parallel
	@parallel.setter
	def parallel(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__parallel = value

	@property
	def dataValid(self) -> bool:
		return self.__dataValid
	@dataValid.setter
	def dataValid(self, value: bool):
		assert isinstance(value, int), "value needs to be bool"
		#
		self.__dataValid = value

	@property
	def packetCountOk(self) -> int:
		return self.__packetCountOk
	@packetCountOk.setter
	def packetCountOk(self, value: int):
		assert isinstance(value, int), "value needs to be integer"
		#
		self.__packetCountOk = value

	@property
	def packetCountErr(self) -> int:
		return self.__packetCountErr
	@packetCountErr.setter
	def packetCountErr(self, value: int):
		assert isinstance(value, int), "value needs to be integer"
		#
		self.__packetCountErr = value

	@property
	def dbgMsg(self) -> str:
		return self.__dbgMsg
	@dbgMsg.setter
	def dbgMsg(self, value: int):
		assert isinstance(value, str), "value needs to be string"
		#
		self.__dbgMsg = value
