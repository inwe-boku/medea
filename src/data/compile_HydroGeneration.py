import os

import pandas as pd

import config as cfg

directory = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'AggregatedGenerationPerType')
df_ror = pd.DataFrame()

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    print(filename)
    if filename.endswith('.csv'):
        df_tmpfile = pd.DataFrame()
        # print(os.path.join(directory, filename))
        ts_agpt = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'AggregatedGenerationPerType',
                                           filename), encoding='utf-16', sep='\t')
        ts_agpt['DateTime'] = pd.to_datetime(ts_agpt['DateTime'])
        ts_agpt.set_index('DateTime', inplace=True)
        splitstr = filename.split('_')
        time = pd.datetime(int(splitstr[0]), int(splitstr[1]), 1)

        if any('ProductionType_Name' in s for s in ts_agpt.columns):
            newcols = [col.replace('ProductionType_Name', 'ProductionType') for col in ts_agpt.columns]
            ts_agpt.columns = newcols

        for reg in cfg.zones:
            df_tmpror = ts_agpt.loc[(ts_agpt['ProductionType'] == 'Hydro Run-of-river and poundage ') & (
                    ts_agpt['MapCode'] == reg), 'ActualGenerationOutput']
            df_tmpres = ts_agpt.loc[(ts_agpt['ProductionType'] == 'Hydro Water Reservoir ') & (
                    ts_agpt['MapCode'] == reg), 'ActualGenerationOutput']
            df_tmppspgen = ts_agpt.loc[(ts_agpt['ProductionType'] == 'Hydro Pumped Storage ') & (
                    ts_agpt['MapCode'] == reg), 'ActualGenerationOutput']
            df_tmppspcon = ts_agpt.loc[(ts_agpt['ProductionType'] == 'Hydro Pumped Storage ') & (
                    ts_agpt['MapCode'] == reg), 'ActualConsumption']
            df_tmpfile[f'ror_{reg}'] = df_tmpror.drop_duplicates()
            df_tmpfile[f'res_{reg}'] = df_tmpres.drop_duplicates()
            df_tmpfile[f'psp_gen_{reg}'] = df_tmppspgen.drop_duplicates()
            df_tmpfile[f'psp_con_{reg}'] = df_tmppspcon.drop_duplicates()
        df_ror = df_ror.append(df_tmpfile)
        del df_tmpror, df_tmpfile

df_ror = df_ror.sort_index()

for reg in cfg.zones:
    df_ror.loc[:, [f'ror_{reg}']] = df_ror.loc[:, [f'ror_{reg}']].interpolate('linear')
df_ror = df_ror.fillna(0)
# resample to hourly frequency
df_ror_hr = df_ror.resample('H').mean()
df_ror_hr = df_ror_hr.interpolate('linear')
df_ror_hr.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'generation_hydro.csv'))
