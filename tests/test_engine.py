import types

from app.engine import force_cpu_deserialization


def fake_torch(load):
    return types.SimpleNamespace(load=load, device=lambda value: f"device:{value}")


def test_force_cpu_deserialization_adds_map_location():
    calls = []

    def fake_load(*args, **kwargs):
        calls.append(kwargs)
        return "loaded"

    torch = fake_torch(fake_load)
    original = torch.load
    with force_cpu_deserialization(torch):
        assert torch.load("checkpoint.pt", weights_only=True) == "loaded"
        assert calls[-1]["map_location"] == "device:cpu"
    assert torch.load is original


def test_force_cpu_deserialization_keeps_explicit_location():
    calls = []
    torch = fake_torch(lambda *a, **kw: calls.append(kw))
    with force_cpu_deserialization(torch):
        torch.load("checkpoint.pt", map_location="meta")
    assert calls[-1]["map_location"] == "meta"
