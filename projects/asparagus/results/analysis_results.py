import os
import pandas as pd
import config as cfg

res = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'results', 'results.csv'))
