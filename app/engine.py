from pathlib import Path
from contextlib import contextmanager
from functools import wraps
import os


@contextmanager
def force_cpu_deserialization(torch_module=None):
    """Work around CUDA-tagged storages in the multilingual checkpoint.

    Chatterbox 0.1.6 calls ``torch.load`` without ``map_location`` for s3gen.pt.
    That crashes on a CPU-only host even though the model itself supports CPU.
    Keep the compatibility patch tightly scoped to checkpoint construction and
    preserve an explicit map_location supplied by upstream.
    """
    if torch_module is None:
        import torch as torch_module

    original_load = torch_module.load

    @wraps(original_load)
    def cpu_load(*args, **kwargs):
        kwargs.setdefault("map_location", torch_module.device("cpu"))
        return original_load(*args, **kwargs)

    torch_module.load = cpu_load
    try:
        yield
    finally:
        torch_module.load = original_load


class ChatterboxEngine:
    sample_rate=24000
    def __init__(self): self.model=None
    def load(self):
        if self.model is None:
            os.environ.setdefault("HF_HUB_OFFLINE","1")
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            with force_cpu_deserialization():
                self.model=ChatterboxMultilingualTTS.from_pretrained(device="cpu")
            self.sample_rate=self.model.sr
    def generate(self,text:str,reference:Path,dest:Path,seed:int=0,**kw):
        import torch
        import soundfile as sf
        self.load(); torch.manual_seed(seed)
        wav=self.model.generate(text,language_id="ru",audio_prompt_path=str(reference),**kw)
        sf.write(dest,wav.squeeze().detach().cpu().numpy(),self.sample_rate)

    def smoke_test(self, dest: Path) -> None:
        """Exercise real inference without being an application voice fallback."""
        import soundfile as sf

        self.load()
        wav = self.model.generate(
            "Проверка локального синтеза на процессоре.", language_id="ru"
        )
        sf.write(dest, wav.squeeze().detach().cpu().numpy(), self.sample_rate)
