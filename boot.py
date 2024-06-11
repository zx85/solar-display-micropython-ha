# boot.py -- run on boot-up
import gc
import sys

sys.path.append("/include/captive_portal")
from captive_portal import CaptivePortal

gc.collect()

portal = CaptivePortal()
portal.start()
