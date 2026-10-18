import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from core_preprocessing import prepare,sequences
from ml.inference import forecast
from core import risk
from optimization.nsga2_optimizer import run_nsga2
d=prepare(pd.read_csv('data/raw/simulated_cold_chain.csv')); d=d[d.sensor_id=='CC-01']; x,y=sequences(d); f=forecast(x[-1]); r=risk(f,'Food'); p,rec=run_nsga2(float(d.temperature.iloc[-1]),float(d.ambient_temperature.iloc[-1]),r['risk_score'])
print('COLDCHAIN AI END-TO-END TEST'); print({'sensor':'CC-01','current_temperature':float(d.temperature.iloc[-1]),'forecast':f,'risk':r,'pareto_solutions':len(p),'recommended':rec}); print('PASS')
