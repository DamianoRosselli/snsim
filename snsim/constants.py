"""This module contains all the constants used in the package."""
import re
from pathlib import Path
from astropy import constants as cst

path_location = Path(__file__).absolute().parent
init_location = path_location / '__init__.py'
VERSION = re.findall(r"__version__ = \"(.*?)\"",
                     init_location.open().read())[0]
SN_SIM_PRINT = '      _______..__   __.         _______. __  .___  ___. \n'
SN_SIM_PRINT += '     /       ||  \\ |  |        /       ||  | |   \\/   | \n'
SN_SIM_PRINT += '    |   (----`|   \\|  |       |   (----`|  | |  \\  /  | \n'
SN_SIM_PRINT += '     \\   \\    |  . `  |        \\   \\    |  | |  |\\/|  | \n'
SN_SIM_PRINT += ' .----)   |   |  |\\   |    .----)   |   |  | |  |  |  | \n'
SN_SIM_PRINT += ' |_______/    |__| \\__|    |_______/    |__| |__|  |__| \n'
SN_SIM_PRINT += f'================================= Version : {VERSION} ====== '

# Light velocity in km/s
C_LIGHT_KMS = cst.c.to('km/s').value

# CMB DIPOLE from Planck18 https://arxiv.org/pdf/1807.06205.pdf
VCMB = 369.82  # km/s
L_CMB = 264.021  # deg
B_CMB = 48.253  # deg

SEP = '###############################################'

""" SNIA from JLA paper """

SNIA_M0={'jla':-19.05}


""" SNII value from Vincenzi et al. 2021 Table 5 """


SNII_M0={'sniipl':{'li11_gaussian':-15.97,'li11_skewed':-17.51},
         'sniib':{'li11_gaussian':-16.69,'li11_skewed':-18.30},
         'sniin':{'li11_gaussian':-17.90, 'li11_skewed':-19.13}}


SNII_mgscatter={'sniipl':{'li11_gaussian':1.31, 'li11_skewed':[2.01,3.18]},
                'sniib':{'li11_gaussian':1.38, 'li11_skewed':[2.03,7.40]},
                'sniin':{'li11_gaussian':0.95, 'li11_skewed':[1.53,6.83]}}


"""Value of h used in the various articles """

h_article={'jla': 0.7,
           'li11': 0.73}



