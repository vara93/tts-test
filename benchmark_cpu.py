#!/usr/bin/env python3
"""Run inside the worker container; never substitutes a listening assessment."""
import argparse,json,os,platform,time,resource,wave
from pathlib import Path
import psutil
from app.engine import ChatterboxEngine

p=argparse.ArgumentParser();p.add_argument("reference",type=Path);p.add_argument("--text",default="Сейчас я произнесу слово: з+амок.");p.add_argument("--runs",type=int,default=3);a=p.parse_args()
info={"cpu":platform.processor() or Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].split(':')[-1].strip(),"vcpus":psutil.cpu_count(),"ram_bytes":psutil.virtual_memory().total,"machine":platform.machine(),"python":platform.python_version(),"threads":os.getenv('OMP_NUM_THREADS')}
t=time.perf_counter();e=ChatterboxEngine();e.load();info['cold_load_seconds']=time.perf_counter()-t
runs=[]
for n in range(a.runs):
 out=Path(f"/tmp/benchmark-{n}.wav");start=time.perf_counter();e.generate(a.text,a.reference,out,seed=n);elapsed=time.perf_counter()-start
 with wave.open(str(out)) as w: duration=w.getnframes()/w.getframerate()
 runs.append({"run":n,"synthesis_seconds":elapsed,"audio_seconds":duration,"rtf":elapsed/duration,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
info['runs']=runs;print(json.dumps(info,ensure_ascii=False,indent=2))
