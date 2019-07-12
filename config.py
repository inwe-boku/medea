# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------- #
# config for power system model suite _medea_
# @author: sweer
# --------------------------------------------------------------------------- #

import os
import platform
import sys

from gams import *

# [model settings]
# set model type -- either 'linear' or 'clustered'
model_type = 'linear'
# set year of underlying simulation data -- currently available: [2013:2017]
year = 2016
# set number of hours to be simulated in each iteration
iter_range = 8760
# set number of iterations for solving a full year (iter_range * iter_num must equal 8760!)
iter_num = 1
# set iteration offset, i.e. number of hours cut off at each iteration-end to avoid last-round effects
iter_offset = 72
# covered regions - currently available: 'AT', 'DE'
regions = ['AT', 'DE']
# long-run (invest) vs short-run (no invest) model version
long_run = True

# [investment conditions]
if long_run:
    invest_renewables = True
    invest_conventionals = True
    invest_storage = True
    invest_ntc = True
else:
    invest_renewables = False
    invest_conventionals = False
    invest_storage = False
    invest_ntc = False

# [package directory]
sys_id = f'{sys.platform} {platform.node()}'
version = GamsWorkspace.api_version
is_64bit = sys.maxsize > 2 ** 32

# ------------------------------------------------------------
# 'folder' and 'gams_sysdir' must be set manually
# ------------------------------------------------------------
if not is_64bit:
    print('System appears to be 32-bit. Expected 64-bit system.')
else:
    if sys_id == 'win32 WINP1218':
        folder = r'Y:\git_repos\medea'
    else:
        folder = r'D:\git_repos\medea'
    gams_sysdir = os.path.join(r'C:\GAMS\win64', version[0:4])
