import json, subprocess, time, wave
from pathlib import Path
import numpy as np
from .db import connect, recover
from .config import DATA
from .engine import ChatterboxEngine
from .text import segments

PRESETS=json.loads((Path(__file__).parent/"presets.json").read_text())
def run():
    recover(); engine=ChatterboxEngine()
    while True:
        with connect() as db:
            row=db.execute("SELECT j.*,p.reference FROM jobs j JOIN profiles p ON p.id=j.profile_id WHERE j.status='queued' ORDER BY j.id LIMIT 1").fetchone()
            if row: db.execute("UPDATE jobs SET status='preparing',started=CURRENT_TIMESTAMP WHERE id=?",(row['id'],))
        if not row: time.sleep(1); continue
        try:
            parts=segments(row['prepared_text']); outdir=DATA/"jobs"/str(row['id']); outdir.mkdir(parents=True,exist_ok=True)
            with connect() as db: db.execute("UPDATE jobs SET status='generating',total=? WHERE id=?",(len(parts),row['id']))
            files=[]
            for i,part in enumerate(parts):
                with connect() as db:
                    if db.execute("SELECT cancel FROM jobs WHERE id=?",(row['id'],)).fetchone()[0]: raise InterruptedError()
                f=outdir/f"{i:05}.wav"; engine.generate(part,Path(row['reference']),f,seed=i,**PRESETS[row['preset']]['model']); files.append(f)
                with connect() as db: db.execute("UPDATE jobs SET done=? WHERE id=?",(i+1,row['id']))
            wav=outdir/"result.wav"; concat(files,wav,PRESETS[row['preset']]['pause_ms'])
            mp3=outdir/"result.mp3"; subprocess.run(["ffmpeg","-v","error","-y","-i",wav,"-codec:a","libmp3lame","-q:a","2",mp3],check=True)
            with connect() as db: db.execute("UPDATE jobs SET status='done',finished=CURRENT_TIMESTAMP,output_wav=?,output_mp3=? WHERE id=?",(str(wav),str(mp3),row['id']))
        except InterruptedError:
            with connect() as db: db.execute("UPDATE jobs SET status='cancelled',finished=CURRENT_TIMESTAMP WHERE id=?",(row['id'],))
        except Exception as e:
            with connect() as db: db.execute("UPDATE jobs SET status='error',error=?,finished=CURRENT_TIMESTAMP WHERE id=?",(str(e)[:1000],row['id']))
def concat(files,dest,pause_ms):
    audio=[]; sr=24000
    for i,f in enumerate(files):
        x,sr=sf_read(f); audio.append(x)
        if i+1<len(files): audio.append(np.zeros(int(sr*pause_ms/1000),dtype=np.float32))
    import soundfile as sf; sf.write(dest,np.concatenate(audio),sr,subtype="PCM_16")
def sf_read(f):
    import soundfile as sf; return sf.read(f,dtype="float32")
if __name__=="__main__": run()

