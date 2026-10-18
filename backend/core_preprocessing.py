import pandas as pd
import numpy as np
FEATURES=['temperature','humidity','ambient_temperature','power_kw','compressor_state','door_open','temperature_delta','rolling_mean','rolling_std','temperature_slope','ambient_difference','power_delta']
def prepare(frame):
 required={'timestamp','sensor_id','temperature'}; missing=required-set(frame.columns)
 if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
 df=frame.copy(); df.timestamp=pd.to_datetime(df.timestamp,utc=True,errors='coerce'); df=df.dropna(subset=['timestamp','sensor_id','temperature']).sort_values(['sensor_id','timestamp']).drop_duplicates(['sensor_id','timestamp'])
 for c in ['humidity','ambient_temperature','power_kw','compressor_state','door_open']:
  if c not in df: df[c]=0
  df[c]=df.groupby('sensor_id')[c].transform(lambda s:s.interpolate().bfill().ffill()).fillna(0)
 g=df.groupby('sensor_id'); df['temperature_delta']=g.temperature.diff().fillna(0); df['rolling_mean']=g.temperature.transform(lambda x:x.rolling(5,min_periods=1).mean()); df['rolling_std']=g.temperature.transform(lambda x:x.rolling(5,min_periods=1).std()).fillna(0); df['temperature_slope']=g.temperature.diff(5).fillna(0)/5; df['ambient_difference']=df.ambient_temperature-df.temperature; df['power_delta']=g.power_kw.diff().fillna(0); return df
def sequences(df,window=60,horizon=15):
 x=df[FEATURES].to_numpy(float); y=df.temperature.to_numpy(float); return np.array([x[i:i+window] for i in range(len(df)-window-horizon)]),np.array([y[i+window:i+window+horizon] for i in range(len(df)-window-horizon)])
