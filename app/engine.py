from pathlib import Path
import os
import soundfile as sf

class ChatterboxEngine:
    sample_rate=24000
    def __init__(self): self.model=None
    def load(self):
        if self.model is None:
            os.environ.setdefault("HF_HUB_OFFLINE","1")
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            self.model=ChatterboxMultilingualTTS.from_pretrained(device="cpu")
            self.sample_rate=self.model.sr
    def generate(self,text:str,reference:Path,dest:Path,seed:int=0,**kw):
        import torch
        self.load(); torch.manual_seed(seed)
        wav=self.model.generate(text,language_id="ru",audio_prompt_path=str(reference),**kw)
        sf.write(dest,wav.squeeze().detach().cpu().numpy(),self.sample_rate)

