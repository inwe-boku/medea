import logging
import os
from itertools import compress

import pysftp
import yaml

import config as cfg
from logging_config import setup_logging

# TODO: check file size and download larger files from ftp

setup_logging()

SERVER = 'sftp-transparency.entsoe.eu'
RAW_DATA_DIR = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw')

CATEGORIES = [
    'ActualGenerationOutputPerUnit',
    'AggregatedGenerationPerType',
    'AggregateFillingRateWaterReservoirs',
    'ScheduledCommercialExchanges'
]

credentials = yaml.load(open(os.path.join(cfg.MEDEA_ROOT_DIR, 'credentials.yml')), Loader=yaml.SafeLoader)
USER = credentials['entsoe']['user']
PWD = credentials['entsoe']['pwd']

# ======================================================================================================================
# sFTP data download
# ----------------------------------------------------------------------------------------------------------------------

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
# connect to entsoe server via sFTP
for cat in CATEGORIES:
    ENTSOE_DIR = '/TP_export/' + cat
    LOCAL_DIR = os.path.join(RAW_DATA_DIR, cat)
    logging.info(f'connecting to {SERVER}')
    with pysftp.Connection(SERVER, username=USER, password=PWD, cnopts=cnopts) as sftp:
        sftp.chdir(ENTSOE_DIR)
        files_entsoe = sftp.listdir()
        os.chdir(LOCAL_DIR)
        files_local = set(os.listdir(LOCAL_DIR))
        # compare to files on disk
        to_download = list(compress(files_entsoe, [item not in files_local for item in files_entsoe]))

        # download files not on disk
        for file in to_download:
            logging.info(f'starting download of {file}...')
            sftp.get(ENTSOE_DIR + '/' + file, os.path.join(RAW_DATA_DIR, cat, file))
            logging.info(f'download of {file} successful')

    sftp.close()
