# %% imports
import logging
import os
import sysconfig
from pathlib import Path
from shutil import copyfile


def init_medea(root_dir):
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
        cfg.write(f"ROOT_DIR = '{root_dir}'\n")

    with open(root_dir / 'credentials.yaml', 'x') as crd:
        crd.write(f"entsoe:\n")
        crd.write(f"\tuser:\n")
        crd.write(f"\tpwd:\n")
        crd.write(f"quandl:\n")
        crd.write(f"\tapikey:\n")
        crd.write(f"copernicus:\n")
        crd.write(f"\turl:\n")
        crd.write(f"\tkey:\n")

    # fetch main gams model
    package_dir = Path(sysconfig.get_path('data'))
    copyfile(package_dir / 'gms' / 'medea_main.gms', root_dir / 'opt' / 'medea_main.gms')
    copyfile(package_dir / 'gms' / 'medea_custom.gms', root_dir / 'opt' / 'medea_custom.gms')
    logging.info('medea sucessfully initialized')


def update_medea_model(root_dir):
    package_dir = Path(sysconfig.get_path('data'))
    copyfile(package_dir / 'gms' / 'medea_main.gms', root_dir / 'opt' / 'medea_main.gms')
    copyfile(package_dir / 'gms' / 'medea_custom.gms', root_dir / 'opt' / 'medea_custom.gms')
    logging.info('medea model updated')
