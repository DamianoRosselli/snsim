"""This module contains all the constants used in the package"""
from astropy import constants as cst
import re
import os

VERSION = re.findall(r"__version__ = \"(.*?)\"",
                     open(os.path.join("snsim", "__init__.py")).read())[0]
SN_SIM_PRINT =  '      _______..__   __.         _______. __  .___  ___. \n'
SN_SIM_PRINT += '     /       ||  \\ |  |        /       ||  | |   \\/   | \n'
SN_SIM_PRINT += '    |   (----`|   \\|  |       |   (----`|  | |  \\  /  | \n'
SN_SIM_PRINT += '     \\   \\    |  . `  |        \\   \\    |  | |  |\\/|  | \n'
SN_SIM_PRINT += ' .----)   |   |  |\\   |    .----)   |   |  | |  |  |  | \n'
SN_SIM_PRINT += ' |_______/    |__| \\__|    |_______/    |__| |__|  |__| \n'
SN_SIM_PRINT += f'================================= Version : {VERSION} ====== '

# Light velocity in km/s
C_LIGHT_KMS = cst.c.to('km/s').value

# just an offset -> set_peakmag(mb=0,'bessellb', 'ab') ->
# offset=2.5*log10(get_x0) change with magsys
SNC_MAG_OFFSET_AB = 10.5020699

VCMB = 369.82
RA_CMB = 266.81
DEC_CMB = 48.253


SEP = '###############################################'
