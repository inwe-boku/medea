import os

import pandas as pd

import config as cfg

directory = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'ScheduledCommercialExchanges')

df_imports = pd.DataFrame(columns=[f'imp_{zn}' for zn in cfg.zones])
df_exports = pd.DataFrame(columns=[f'exp_{zn}' for zn in cfg.zones])
df_X_endo = pd.DataFrame(columns=[f'{zn}->{zzn}' for zn in cfg.zones for zzn in cfg.zones if zn != zzn])

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    print(filename)
    if filename.endswith('.csv'):
        df_flows = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'ScheduledCommercialExchanges',
                                            filename), sep='\t', encoding='utf-16')
        df_flows['DateTime'] = pd.to_datetime(df_flows['DateTime'])
        # for each zone: sum import and export flows from / to all other zones except the ones included in model
        # 1) import flows
        # for Germany: select (InMapCode == 'DE') & (InAreaTypeCode == 'CTY') & (OutAreaTypeCode == 'CTY') &
        # (OutMapCode not in cfg.zones)
        # InAreaTypeCode: 'CTA' - Control Area, 'CTY' - Country, 'BZN' - Bidding Zone
        # InMapCode: 'DE_50HzT', 'DE_AT_LU', 'DE', 'DE_TenneT_GER', 'AT', 'DE_Amprion', 'DE_TransnetBW'
        df_imp = pd.DataFrame(columns=[f'imp_{zn}' for zn in cfg.zones])
        df_exp = pd.DataFrame(columns=[f'exp_{zn}' for zn in cfg.zones])
        for zone in cfg.zones:
            # imports
            df_i = df_flows.loc[(df_flows['InMapCode'] == zone) &
                                (~df_flows['OutMapCode'].str.contains('|'.join(cfg.zones))), :]
            if len(df_i['OutAreaTypeCode'].unique()) > 1:
                if 'CTY' in df_i['OutAreaTypeCode'].unique():
                    df_i = df_i.loc[df_i['OutAreaCode'] == 'CTY']
                elif 'CTA' in df_i['OutAreaTypeCode'].unique():
                    df_i = df_i.loc[df_i['OutAreaCode'] == 'CTA']
                else:
                    raise ValueError('Imports: Out Area not uniquely defined. Check OutArea for duplicates.')
            if len(df_i['InAreaTypeCode'].unique()) > 1:
                if 'CTY' in df_i['InAreaTypeCode'].unique():
                    df_i = df_i.loc[df_i['InAreaCode'] == 'CTY']
                elif 'CTA' in df_i['InAreaTypeCode'].unique():
                    df_i = df_i.loc[df_i['InAreaCode'] == 'CTA']
                else:
                    raise ValueError('Imports: In Area not uniquely defined. Check InArea for duplicates.')
            df_imp[f'imp_{zone}'] = (df_i[['DateTime', 'OutMapCode',
                                           'Capacity']].groupby('DateTime').sum()).loc[:, 'Capacity']

            # exports
            df_e = df_flows.loc[(df_flows['OutMapCode'] == zone) &
                                (~df_flows['InMapCode'].str.contains('|'.join(cfg.zones))), :]
            if len(df_e['OutAreaTypeCode'].unique()) > 1:
                if 'CTY' in df_e['OutAreaTypeCode'].unique():
                    df_e = df_e.loc[df_e['OutAreaCode'] == 'CTY']
                elif 'CTA' in df_e['OutAreaTypeCode'].unique():
                    df_e = df_e.loc[df_e['OutAreaCode'] == 'CTA']
                else:
                    raise ValueError('Exports: Out Area not uniquely defined. Check OutArea for duplicates.')
            if len(df_e['InAreaTypeCode'].unique()) > 1:
                if 'CTY' in df_e['InAreaTypeCode'].unique():
                    df_e = df_e.loc[df_e['InAreaCode'] == 'CTY']
                elif 'CTA' in df_e['InAreaTypeCode'].unique():
                    df_e = df_e.loc[df_e['InAreaCode'] == 'CTA']
                else:
                    raise ValueError('Exports : In Area not uniquely defined. Check InArea for duplicates.')
            df_exp[f'exp_{zone}'] = (df_e[['DateTime', 'OutMapCode',
                                           'Capacity']].groupby('DateTime').sum()).loc[:, 'Capacity']
        df_imports = df_imports.append(df_imp)
        df_exports = df_exports.append(df_exp)

        df_x = pd.DataFrame(
            columns=[f'{zn}->{zzn}' for zn in cfg.zones for zzn in cfg.zones if zn != zzn])
        for zone in cfg.zones:
            # flows between endogenous zones
            bool_out = (df_flows['OutMapCode'] == zone) & (df_flows['OutAreaTypeCode'] == 'CTY')
            for zzone in cfg.zones:
                if zone != zzone:
                    bool_in = (df_flows['InMapCode'] == zzone) & (df_flows['InAreaTypeCode'] == 'CTY')
                    df_xtmp = df_flows.loc[bool_out & bool_in, ['DateTime', 'Capacity']].groupby('DateTime').sum()
                    df_x[f'{zone}->{zzone}'] = df_xtmp['Capacity']
        df_X_endo = df_X_endo.append(df_x)

df_imports.index = pd.DatetimeIndex(df_imports.index)
df_imports = df_imports.sort_index()
df_exports.index = pd.DatetimeIndex(df_exports.index)
df_exports = df_exports.sort_index()
df_X_endo.index = pd.DatetimeIndex(df_X_endo.index)
df_X_endo = df_X_endo.sort_index()

df_flows = pd.concat([df_imports, df_exports], axis=1)
df_flows.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'commercial_flows.csv'))
df_X_endo.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'commercial_flows_endogenous.csv'))
