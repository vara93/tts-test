from pathlib import Path

from .engine import ChatterboxEngine


def main() -> None:
    output = Path("/data/install-smoke.wav")
    ChatterboxEngine().smoke_test(output)
    if not output.is_file() or output.stat().st_size < 1024:
        raise RuntimeError("Smoke WAV не создан или пуст")
    print(f"Настоящий CPU smoke WAV создан: {output} ({output.stat().st_size} байт)")


if __name__ == "__main__":
    main()
