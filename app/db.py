import sqlite3
from .config import DATA, DB

SCHEMA="""
CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY,name TEXT NOT NULL,reference TEXT NOT NULL,created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,profile_id INTEGER NOT NULL,source_text TEXT NOT NULL,prepared_text TEXT NOT NULL,preset TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued',done INTEGER NOT NULL DEFAULT 0,total INTEGER NOT NULL DEFAULT 0,error TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP,started TEXT,finished TEXT,output_wav TEXT,output_mp3 TEXT,cancel INTEGER NOT NULL DEFAULT 0,FOREIGN KEY(profile_id) REFERENCES profiles(id));
CREATE TABLE IF NOT EXISTS dictionary(word TEXT PRIMARY KEY,pronunciation TEXT NOT NULL);
"""
def connect():
    DATA.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=30); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.executescript(SCHEMA); return db

def recover():
    with connect() as db:
        db.execute("UPDATE jobs SET status='error',error='Сервис был перезапущен во время генерации',finished=CURRENT_TIMESTAMP WHERE status IN ('preparing','generating')")

