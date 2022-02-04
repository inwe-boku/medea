# %% imports
import os
import sysconfig
import logging
from medea.logging_config import setup_logging
from pathlib import Path
from shutil import copyfile

setup_logging()

def medea_init(root_dir):
    """
    Creates a directory structure for a medea project
    :param root_dir: String or Path-object with the project's root directory
    :return:
    """
    root_dir = Path(root_dir)
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    os.makedirs(root_dir / 'data')
    os.makedirs(root_dir / 'data' / 'results')
    os.makedirs(root_dir / 'doc')
    os.makedirs(root_dir / 'doc' / 'figures')
    os.makedirs(root_dir / 'opt')
    os.makedirs(root_dir / 'src')
    with open(root_dir / 'config.py', 'x') as cfg:
        cfg.write(f"'ROOT_DIR = {root_dir}\n'")

    # fetch main gams model
    package_dir = Path(sysconfig.get_path('data'))
    copyfile(package_dir / 'gms' / 'medea_main.gms', root_dir / 'opt' / 'medea_main.gms')
    copyfile(package_dir / 'gms' / 'medea_custom.gms', root_dir / 'opt' / 'medea_custom.gms')
    logging.info('medea sucessfully initialized')
