import pytest

from strideai.core.models import ThreatModel
from strideai.report import llm_writer
from strideai.report.llm_writer import LLMError, write_report


class _Block:
    type = "text"
    text = "# Relatório gerado pelo LLM"


class _Response:
    content = [_Block()]


class _FakeMessages:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self.fail:
            raise RuntimeError("api down")
        return _Response()


class _FakeClient:
    def __init__(self, fail: bool = False):
        self.messages = _FakeMessages(fail)


def test_write_report_returns_llm_text(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(llm_writer, "_get_client", lambda: fake)
    md = write_report(ThreatModel())
    assert md == "# Relatório gerado pelo LLM"
    # The prompt must carry the structured threat model, not the raw image
    assert "components" in str(fake.messages.last_kwargs["messages"])


def test_write_report_wraps_failures(monkeypatch):
    monkeypatch.setattr(llm_writer, "_get_client", lambda: _FakeClient(fail=True))
    with pytest.raises(LLMError):
        write_report(ThreatModel())
