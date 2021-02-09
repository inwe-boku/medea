import logging.config
import os

import config as cfg

LOG_FILE = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'logfile.log')


def setup_logging(fname=LOG_FILE):
    no_color = '\33[m'
    red, green, orange, blue, purple, lblue, grey = (
        map('\33[%dm'.__mod__, range(31, 38)))

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)-4s - '
                          '%(name)-4s - %(message)s'
            },
            'color': {
                'format': '{}[%(asctime)s]{} {}%(levelname)-5s{} - '
                          '{}%(name)-5s{}: %(message)s'.format(green, no_color, purple, no_color, orange, no_color)
            }
        },
        'handlers': {
            'stream': {
                'class': 'logging.StreamHandler',
                'formatter': 'color',
            }
        },
        'root': {
            'handlers': ['stream'],
            'level': logging.INFO,
        },
    }
    if fname is not None:
        logging_config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'level': logging.DEBUG,
            'filename': fname,
        }

        logging_config['root']['handlers'].append('file')

    logging.config.dictConfig(logging_config)
