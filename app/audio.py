import subprocess, wave
from pathlib import Path
import numpy as np
from .config import DATA

def decode(src: Path, profile_id: int) -> Path:
    out=DATA/"profiles"/str(profile_id)/"reference.wav"; out.parent.mkdir(parents=True,exist_ok=True)
    p=subprocess.run(["ffmpeg","-v","error","-y","-i",str(src),"-ac","1","-ar","24000",str(out)],capture_output=True,text=True)
    if p.returncode: raise ValueError("FFmpeg не смог декодировать запись: "+p.stderr[-300:])
    with wave.open(str(out)) as w:
        seconds=w.getnframes()/w.getframerate(); raw=w.readframes(w.getnframes())
    if not 3 <= seconds <= 60: raise ValueError("Запись должна длиться от 3 до 60 секунд")
    x=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768
    if np.sqrt(np.mean(x*x)) < .003: raise ValueError("Запись почти полностью состоит из тишины")
    if np.mean(np.abs(x)>.995)>.01: raise ValueError("В записи слишком много клиппинга")
    return out

