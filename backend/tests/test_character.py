"""Character endpoint tests — SSE framing, error handling, validation."""

from unittest.mock import patch

BODY = {
    "question": "What is the GIL?",
    "answer": "A global lock in CPython.",
    "feedback": "Accurate.",
    "score": 8,
    "lang": "ua",
}

URL = "/api/v1/character/react/stream"


class _FakeStream:
    """Mimics anthropic's messages.stream() async context manager."""

    def __init__(self, tokens):
        self._tokens = tokens

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    @property
    def text_stream(self):
        async def gen():
            for token in self._tokens:
                yield token

        return gen()


async def test_react_stream_sse_framing(client, auth_headers):
    with patch("app.api.routes.character._client") as mock_client:
        mock_client.messages.stream.return_value = _FakeStream(["Nice", " work"])
        resp = await client.post(URL, json=BODY, headers=auth_headers)

    assert resp.status_code == 200
    assert 'data: {"token": "Nice"}' in resp.text
    assert "data: [DONE]" in resp.text


async def test_react_stream_error_does_not_leak_exception(client, auth_headers):
    with patch("app.api.routes.character._client") as mock_client:
        mock_client.messages.stream.side_effect = RuntimeError("secret internal detail")
        resp = await client.post(URL, json=BODY, headers=auth_headers)

    assert "generation_failed" in resp.text
    assert "secret internal detail" not in resp.text
    assert "data: [DONE]" in resp.text


async def test_react_rejects_unknown_lang(client, auth_headers):
    resp = await client.post(URL, json={**BODY, "lang": "de"}, headers=auth_headers)
    assert resp.status_code == 422


async def test_react_rejects_out_of_range_score(client, auth_headers):
    resp = await client.post(URL, json={**BODY, "score": 15}, headers=auth_headers)
    assert resp.status_code == 422


async def test_react_rejects_oversized_answer(client, auth_headers):
    resp = await client.post(URL, json={**BODY, "answer": "x" * 6000}, headers=auth_headers)
    assert resp.status_code == 422


async def test_react_requires_auth(client):
    resp = await client.post(URL, json=BODY)
    assert resp.status_code == 401
