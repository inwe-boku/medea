import logging
import os
from itertools import compress

import pysftp
import yaml

from logging_config import setup_logging
from src.utils.data_processing import medea_path

# TODO: check file size and download larger files from ftp
# TODO: download zipped csv and unpack after download

setup_logging()

SERVER = 'sftp-transparency.entsoe.eu'
RAW_DATA_DIR = medea_path('data', 'raw')

CATEGORIES = [
    'ActualGenerationOutputPerGenerationUnit_16.1.A',
    'AggregatedGenerationPerType_16.1.B_C',
    'AggregatedFillingRateOfWaterReservoirsAndHydroStoragePlants_16.1.D',
    'TotalCommercialSchedules_12.1.F'
    #    'ScheduledCommercialExchanges'
]

credentials = yaml.load(open(medea_path('credentials.yml')), Loader=yaml.SafeLoader)
USER = credentials['entsoe']['user']
PWD = credentials['entsoe']['pwd']


# ======================================================================================================================
# %% sFTP data download
# ----------------------------------------------------------------------------------------------------------------------
def get_entsoe(connection_string, user, pwd, category, directory):
    """
    downloads dataset from ENTSO-E's transparency data sftp server.
    contact ENTSO-E to receive login credentials.
    :param connection_string: url of ENTSO-E transparency server, as of May 1, 2020: 'sftp-transparency.entsoe.eu'
    :param user: user name required for connecting with sftp server
    :param pwd: password required for connecting with sftp server
    :param category: ENTSO-E data category to be downloaded
    :param directory: directory where downloaded data is saved to. A separate subdirectory is created for each category
    :return: downloaded dataset(s) in dir
    """
    # check if local_dir exists and create if it doesn't
    local_dir = os.path.join(directory, category)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    #
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # connect to entsoe server via sFTP
    entsoe_dir = f'/TP_export/{category}'
    logging.info(f'connecting to {connection_string}')
    with pysftp.Connection(connection_string, username=user, password=pwd, cnopts=cnopts) as sftp:
        sftp.chdir(entsoe_dir)
        files_entsoe = sftp.listdir()
        os.chdir(local_dir)
        files_local = set(os.listdir(local_dir))
        # compare to files on disk
        to_download = list(compress(files_entsoe, [item not in files_local for item in files_entsoe]))
        # download files not on disk
        for file in to_download:
            logging.info(f'starting download of {file}...')
            sftp.get(f'{entsoe_dir}/{file}', os.path.join(RAW_DATA_DIR, category, file))
            logging.info(f'download of {file} successful')

    sftp.close()


# %% download data
for cat in CATEGORIES:
    get_entsoe(SERVER, USER, PWD, cat, RAW_DATA_DIR)
