import bson
import numpy as np
import pandas as pd


# TODO: Make this cleaning function entirely dependent on configuration
def clean_data(df, fill=True):
    """
    Fills in missing values in input dataframe
    :param df: pandas dataframe
    :param fill: (bool) If true then fills in values in the dataframe using either forward fill, back, fill, and

    :returns cleaned dataframe.
    """

    df = df.copy(deep=True)
    if not df.empty:
        by_device_name = df.groupby(['mac_address', 'device_base_address'])

        # Fill the following columns using last one carried forward
        fill_cols = ['COMP_RLY', 'HEATCTRL', 'FAN_CTRL', 'WHTRENAB', 'WHTRCNFG', 'WHTRSETP', 'WHTRMODE',
                     'SHUTOFFV', 'SHUTOPEN', 'SHUTCLOS', 'ANODESTS', 'UNITTYPE', 'HOTWATER']

        fill_cols = [col_name for col_name in fill_cols if col_name in df.columns.values]
        if fill and fill_cols:
            df.loc[:, fill_cols] = by_device_name[fill_cols].transform(func=pd.Series.ffill)

        # Fill these columns using bi-directional fill
        fill_cols = ['LOELSIZE', 'UPELSIZE', 'SW_VERSN', 'PRODSERN', 'PRODDESC', 'PRODMODN']
        fill_cols = [col_name for col_name in fill_cols if col_name in df.columns.values]

        if fill and fill_cols:
            df.loc[:, fill_cols] = by_device_name[fill_cols].ffill().bfill()

        # Fill these columns by linear interpolation using timestamp as the x-value
        fill_cols = ['SUCTIONT', 'DISCTEMP', 'I_RMSVAL', 'SECCOUNT', 'AMBIENTT', 'EVAPTEMP', 'EXACTUAL', 'LOHTRTMP',
                     'UPHTRTMP', 'POWRWATT', 'TOTALKWH', 'ANODEA2D', 'HRSLOHTR', 'HRSHIFAN', 'HRSLOFAN', 'HRS_COMP',
                     'HRSUPHTR']
        fill_cols = [col_name for col_name in fill_cols if col_name in df.columns.values]

        # TODO change interpolation method to not use linear interpolation because the data points are not equally spaced
        if fill and fill_cols:
            df.loc[:, fill_cols] = by_device_name[fill_cols].apply(pd.DataFrame.interpolate)

        alarm_cols = [col_name for col_name in df.columns.values if col_name.startswith('ALARM_')]
        df[alarm_cols] = df[alarm_cols].apply(lambda x: x.str.strip())

    return df


def read_bson(file_path):
    """
    Reads a mongo db dump file (binary bson format) and returns a cleaned dataframe.
    :para
    Example:
            data = read_bson(os.path.join(directory, 'history.bson'))
    """
    with open(file_path, 'rb') as infile:
        data = bson.decode_all(infile.read())

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df.timestamp, utc=True)
    df = df.set_index(['_id']).sort_index(axis=0).drop(['cloud2_account_id', 'SYSCLOUD'], axis=1)

    return df


def get_total_alarm_count(df_alarms):
    """
    :param df_alarms pandas DataFrame of raw data including alarm columns
    """

    df = df_alarms.loc[:, ['ALARM_01', 'ALARM_02', 'ALARM_03', 'ALARM_04']].melt(
        value_name='alarm_text', var_name='alarm_register').replace('', np.nan).dropna(how='any')
    if df.shape[0]:
        df = df['alarm_text'].str.split(' ', n=1, expand=True).rename(columns={0: "alarm_code", 1: "alarm_text"})
        df = df.groupby('alarm_code').count().sort_values('alarm_text', ascending=False).reset_index()
        df = df.loc[df.alarm_text > 0, :]
    else:
        df = pd.DataFrame({"alarm_code": [], "alarm_text": []})

    return df
