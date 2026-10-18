import torch
from pathlib import Path
from core_preprocessing import FEATURES
from ml.mad_tcn import MADTCN

_model = None

def _get_model_path():
    for base in [Path('.'), Path(__file__).resolve().parent.parent.parent, Path(__file__).resolve().parent.parent]:
        p = base / 'models' / 'mad_tcn_best.pt'
        if p.exists():
            return p
    return Path('models/mad_tcn_best.pt')

def forecast(sequence):
    global _model
    if _model is None:
        _model = MADTCN(len(FEATURES))
        _model.load_state_dict(torch.load(_get_model_path(), map_location='cpu', weights_only=True))
        _model.eval()
    with torch.no_grad():
        return _model(torch.tensor(sequence, dtype=torch.float32).unsqueeze(0)).squeeze().tolist()

