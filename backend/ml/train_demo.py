from pathlib import Path
import json,torch,pandas as pd
from core_preprocessing import prepare,sequences,FEATURES
from ml.mad_tcn import MADTCN
def main():
 d=prepare(pd.read_csv('data/raw/simulated_cold_chain.csv')); d=d[d.sensor_id=='CC-01']; x,y=sequences(d); n=int(len(x)*.8); m=MADTCN(len(FEATURES)); opt=torch.optim.Adam(m.parameters(),lr=1e-3); loss=torch.nn.MSELoss()
 for _ in range(3):
  for i in range(0,n,128): opt.zero_grad(); z=loss(m(torch.tensor(x[i:i+128],dtype=torch.float32)),torch.tensor(y[i:i+128],dtype=torch.float32)); z.backward(); opt.step()
 with torch.no_grad(): p=m(torch.tensor(x[n:],dtype=torch.float32)); a=torch.tensor(y[n:],dtype=torch.float32); mae=float((p-a).abs().mean()); rmse=float(((p-a)**2).mean().sqrt())
 Path('models').mkdir(exist_ok=True); torch.save(m.state_dict(),'models/mad_tcn_best.pt'); Path('models/metrics.json').write_text(json.dumps({'mae':mae,'rmse':rmse,'dataset':'SIMULATION'})); print(json.dumps({'mae':mae,'rmse':rmse}))
if __name__=='__main__': main()
