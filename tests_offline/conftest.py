import importlib, socket, sys
from pathlib import Path
from unittest import mock
import pytest

ROOT = Path(__file__).resolve().parent.parent
MODULES = ["test_local_benchmark", "test_llm_judge", "test_security", "test_rag_hallucinations"]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def _blocked(*a, **k):
        raise AssertionError("network access attempted in offline test")
    monkeypatch.setattr(socket.socket, "connect", _blocked)


@pytest.fixture
def load_module(monkeypatch):
    """Import a root test module with ollama.list patched, cwd = repo root."""
    def _load(name, installed=None, list_error=None):
        import ollama
        if list_error:
            fake = mock.Mock(side_effect=list_error)
        else:
            fake = mock.Mock(return_value={"models": installed or []})
        monkeypatch.setattr(ollama, "list", fake)
        monkeypatch.setattr(ollama, "chat", mock.Mock(side_effect=AssertionError("unmocked ollama.chat")))
        monkeypatch.chdir(ROOT)
        monkeypatch.syspath_prepend(str(ROOT))
        sys.modules.pop(name, None)
        mod = importlib.import_module(name)
        monkeypatch.setitem(sys.modules, name, mod)  # restored/removed afterwards
        return mod
    yield _load
    for n in MODULES:
        sys.modules.pop(n, None)


@pytest.fixture
def chat(monkeypatch):
    """Install a fake ollama.chat returning queued answers; returns the Mock."""
    def _install(*answers):
        import ollama
        m = mock.Mock(side_effect=[{"message": {"content": a}} for a in answers])
        monkeypatch.setattr(ollama, "chat", m)
        return m
    return _install
