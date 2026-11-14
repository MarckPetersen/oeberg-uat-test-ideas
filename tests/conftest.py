from types import SimpleNamespace

import pytest

from uat.ai import ClaudeClient, UATIdeasResponse
from uat.config import Settings


def make_settings(tmp_path, **kw):
    base = dict(has_api_key=True, model="test-model", data_dir=str(tmp_path), max_calls_per_day=30,
                max_input_chars=4000, max_output_tokens=2000)
    base.update(kw)
    return Settings(**base)


class FakeMessages:
    """Stands in for anthropic.Anthropic().messages – never calls the paid API."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0) if self.responses else ideas_response()
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, SimpleNamespace):
            return item
        return SimpleNamespace(parsed_output=item, stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=100, output_tokens=50))


def ideas_response(n=5, note=None):
    return UATIdeasResponse(ideas=[f"Verify that scenario {i} works for the business user." for i in range(1, n + 1)],
                            note=note)


def fake_client(tmp_path, *responses, **kw):
    messages = FakeMessages(responses)
    return ClaudeClient(make_settings(tmp_path, **kw), client=SimpleNamespace(messages=messages)), messages


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)
