FROM python:3.11.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/models OMP_NUM_THREADS=4
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /studio
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY app app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--proxy-headers"]
