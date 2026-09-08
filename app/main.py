from pathlib import Path
import shutil, tempfile
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import TOKEN, MAX_UPLOAD, DATA
from .db import connect, recover
from .audio import decode
from .text import prepare, validate_stress

app=FastAPI(title="Голосовая студия",docs_url="/api/docs")
@app.on_event("startup")
def startup(): recover()
def auth(authorization:str|None):
    if authorization != f"Bearer {TOKEN}": raise HTTPException(401,"Неверный пароль")
@app.get("/api/health")
def health(): return {"ok":True,"engine":"chatterbox-multilingual","device":"cpu"}
@app.get("/api/profiles")
def profiles(authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db: return [dict(x) for x in db.execute("SELECT id,name,created FROM profiles ORDER BY id DESC")]
@app.post("/api/profiles")
async def profile(name:str=Form(...),audio:UploadFile=File(...),authorization:str|None=Header(None)):
    auth(authorization)
    suffix=Path(audio.filename or "audio").suffix; tmp=Path(tempfile.mkstemp(suffix=suffix)[1]); size=0
    try:
        with tmp.open("wb") as f:
            while chunk:=await audio.read(1024*1024):
                size+=len(chunk)
                if size>MAX_UPLOAD: raise HTTPException(413,"Файл слишком велик")
                f.write(chunk)
        with connect() as db:
            cur=db.execute("INSERT INTO profiles(name,reference) VALUES(?,?)",(name,"pending")); pid=cur.lastrowid
        ref=decode(tmp,pid)
        with connect() as db: db.execute("UPDATE profiles SET reference=? WHERE id=?",(str(ref),pid))
        return {"id":pid,"name":name}
    except Exception:
        if 'pid' in locals():
            shutil.rmtree(DATA/"profiles"/str(pid),ignore_errors=True)
            with connect() as db: db.execute("DELETE FROM profiles WHERE id=?",(pid,))
        raise
    finally: tmp.unlink(missing_ok=True)
@app.delete("/api/profiles/{pid}")
def delete_profile(pid:int,authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db:
        if db.execute("SELECT 1 FROM jobs WHERE profile_id=? AND status IN ('queued','preparing','generating')",(pid,)).fetchone(): raise HTTPException(409,"Профиль используется")
        db.execute("DELETE FROM jobs WHERE profile_id=?",(pid,)); db.execute("DELETE FROM profiles WHERE id=?",(pid,))
    shutil.rmtree(DATA/"profiles"/str(pid),ignore_errors=True); return {"ok":True}
@app.get("/api/profiles/{pid}/audio")
def profile_audio(pid:int,authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db: r=db.execute("SELECT reference FROM profiles WHERE id=?",(pid,)).fetchone()
    if not r:
        raise HTTPException(404)
    return FileResponse(r[0])
@app.get("/api/dictionary")
def dictionary(authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db:return [dict(x) for x in db.execute("SELECT * FROM dictionary")]
@app.put("/api/dictionary/{word}")
def dict_put(word:str,body:dict,authorization:str|None=Header(None)):
    auth(authorization); validate_stress(body.get("pronunciation",""))
    with connect() as db: db.execute("INSERT INTO dictionary VALUES(?,?) ON CONFLICT(word) DO UPDATE SET pronunciation=excluded.pronunciation",(word.casefold(),body["pronunciation"]))
    return {"ok":True}
@app.get("/api/jobs")
def jobs(authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db:return [dict(x) for x in db.execute("SELECT id,profile_id,source_text,prepared_text,preset,status,done,total,error,created,started,finished FROM jobs ORDER BY id DESC LIMIT 100")]
@app.post("/api/jobs")
def job(body:dict,authorization:str|None=Header(None)):
    auth(authorization); source=body.get("text","")
    if not source or len(source)>100000: raise HTTPException(422,"Текст должен содержать 1–100000 символов")
    if body.get("preset") not in ('fairy','poem','lullaby'): raise HTTPException(422,"Неизвестный режим")
    try:
        with connect() as db:
            d={x['word']:x['pronunciation'] for x in db.execute("SELECT * FROM dictionary")}; ready=prepare(source,d)
            cur=db.execute("INSERT INTO jobs(profile_id,source_text,prepared_text,preset,status) VALUES(?,?,?,?, 'queued')",(body['profile_id'],source,ready,body['preset']))
            return {"id":cur.lastrowid,"prepared_text":ready}
    except ValueError as e: raise HTTPException(422,str(e))
@app.post("/api/jobs/{jid}/cancel")
def cancel(jid:int,authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db: db.execute("UPDATE jobs SET cancel=1,status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END WHERE id=?",(jid,))
    return {"ok":True}
@app.get("/api/jobs/{jid}/{fmt}")
def result(jid:int,fmt:str,authorization:str|None=Header(None)):
    auth(authorization)
    if fmt not in ('wav','mp3'): raise HTTPException(404)
    with connect() as db:r=db.execute(f"SELECT output_{fmt} FROM jobs WHERE id=? AND status='done'",(jid,)).fetchone()
    if not r or not r[0]: raise HTTPException(404)
    return FileResponse(r[0],filename=f"studio-{jid}.{fmt}")
app.mount("/",StaticFiles(directory=Path(__file__).parent/"static",html=True),name="static")
