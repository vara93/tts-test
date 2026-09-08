import os
import pytest
os.environ['TTS_DATA']='/tmp/tts-studio-test';os.environ['STUDIO_PASSWORD']='test'
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from app.main import app
def test_auth_and_health():
 c=TestClient(app);assert c.get('/api/health').status_code==200;assert c.get('/api/jobs').status_code==401
def test_bad_stress():
 c=TestClient(app);h={'Authorization':'Bearer test'}
 assert c.post('/api/jobs',headers=h,json={'profile_id':1,'text':'зам+к','preset':'fairy'}).status_code==422
