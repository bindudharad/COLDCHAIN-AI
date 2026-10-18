from pathlib import Path
import numpy as np
import pandas as pd
def main():
 rng=np.random.default_rng(42); periods=4000; ts=pd.date_range('2026-01-01',periods=periods,freq='min'); frames=[]
 for sid in range(3):
  ambient=23+4*np.sin(np.arange(periods)/240)+rng.normal(0,.45,periods); door=(rng.random(periods)<.018).astype(int); temp=np.empty(periods); temp[0]=3.5+sid*.2
  for i in range(1,periods):
   compressor=temp[i-1]>3.8; temp[i]=temp[i-1]+.018*(ambient[i]-temp[i-1])- .32*compressor + .16*door[i]+rng.normal(0,.035)
  frames.append(pd.DataFrame({'timestamp':ts,'sensor_id':f'CC-{sid+1:02}','temperature':temp,'humidity':70+rng.normal(0,3,periods),'ambient_temperature':ambient,'power_kw':.25+(temp>3.8)*.75+door*.12,'compressor_state':(temp>3.8).astype(int),'door_open':door,'product_type':'Food','location':'DEMONSTRATION / SIMULATION WAREHOUSE'}))
 out=Path(__file__).parents[1]/'data'/'raw'; out.mkdir(parents=True,exist_ok=True); pd.concat(frames).to_csv(out/'simulated_cold_chain.csv',index=False); print('Generated 12000 DEMONSTRATION / SIMULATION records')
if __name__=='__main__': main()
