# CPU benchmark

Результаты целевой VM отсутствуют и не выдумываются. Команда:

```bash
docker compose exec worker python benchmark_cpu.py /data/profiles/1/reference.wav --runs 5 | tee data/benchmark.json
```

Скрипт фиксирует модель CPU, x86_64, vCPU, RAM, Python, число потоков, холодную загрузку, время синтеза, длительность WAV, peak RSS и `RTF = synthesis/audio` (меньше лучше; >1 медленнее реального времени). Reference preparation сейчас выполняется при загрузке профиля; измерьте дополнительно длительность POST `/api/profiles`. Для поиска накопления сравните `peak_rss_kib` минимум пяти последовательных запусков. Не публикуйте показатель без имени CPU и параметров.

