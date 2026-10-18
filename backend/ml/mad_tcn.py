"""Multi-scale adaptive dilated temporal convolutional forecaster."""
import torch
from torch import nn
class CausalBlock(nn.Module):
 def __init__(self,c,d):
  super().__init__(); self.conv=nn.Conv1d(c,c,3,padding=2*d,dilation=d); self.norm=nn.BatchNorm1d(c); self.act=nn.GELU()
 def forward(self,x): return x+self.act(self.norm(self.conv(x)[:,:,:x.size(-1)]))
class MADTCN(nn.Module):
 def __init__(self,features,hidden=32,horizon=15):
  super().__init__(); self.project=nn.Conv1d(features,hidden,1); self.branches=nn.ModuleList([nn.Conv1d(hidden,hidden,3,padding=2*d,dilation=d) for d in (1,2,4,8)]); self.gate=nn.Sequential(nn.AdaptiveAvgPool1d(1),nn.Conv1d(hidden,4,1),nn.Softmax(dim=1)); self.residual=nn.Sequential(CausalBlock(hidden,1),CausalBlock(hidden,2)); self.head=nn.Linear(hidden,horizon)
 def forward(self,x):
  x=self.project(x.transpose(1,2)); weights=self.gate(x); scales=torch.stack([b(x)[:,:,:x.size(-1)] for b in self.branches],1); x=(scales*weights.unsqueeze(2)).sum(1); return self.head(self.residual(x)[:,:,-1])
