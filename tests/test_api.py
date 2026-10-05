import asyncio

import aiohttp
import pytest

from custom_components.foodisco.api import (
    CannotConnect,
    FoodiscoApi,
    InvalidAuth,
    InvalidCode,
    RateLimited,
)


class FakeResponse:
    def __init__(self, status, body=None, headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def json(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, response=None, error=None):
        self.calls = []
        self._response = response
        self._error = error

    def request(self, method, url, headers=None, json=None):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json})
        if self._error:
            raise self._error
        return self._response


def api(response=None, error=None, base="https://x.test/functions/v1/"):
    session = FakeSession(response, error)
    return FoodiscoApi(session, base), session


def run(coro):
    return asyncio.run(coro)


def test_pair_posts_the_code_without_credentials_and_returns_the_tokens():
    tokens = {"read_token": "ha_r", "events_token": "ha_e", "account_id": "u1", "display_name": "Sascha"}
    client, session = api(FakeResponse(200, tokens))
    assert run(client.pair("ABCD-EFGH")) == tokens
    call = session.calls[0]
    assert call["method"] == "POST" and call["url"] == "https://x.test/functions/v1/ha-pair"
    assert call["json"] == {"code": "ABCD-EFGH"} and call["headers"] == {}


def test_status_sends_the_read_token_as_bearer():
    client, session = api(FakeResponse(200, {"kcal_today": 1}))
    assert run(client.status("ha_r")) == {"kcal_today": 1}
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["headers"] == {"Authorization": "Bearer ha_r"}


def test_report_event_posts_the_event_with_the_events_token():
    client, session = api(FakeResponse(200, {"ok": True}))
    run(client.report_event("ha_e", "oven_finished"))
    call = session.calls[0]
    assert call["url"].endswith("/ha-event") and call["json"] == {"event": "oven_finished"}
    assert call["headers"] == {"Authorization": "Bearer ha_e"}


def test_a_bad_code_is_its_own_error_but_only_for_pairing():
    client, _ = api(FakeResponse(400, {"error": "invalid_code"}))
    with pytest.raises(InvalidCode):
        run(client.pair("ABCD-EFGH"))
    # a 400 anywhere else is just a failure, not "your code is wrong"
    with pytest.raises(CannotConnect):
        run(client.report_event("ha_e", "nope"))


def test_a_revoked_token_asks_for_re_pairing():
    client, _ = api(FakeResponse(401, {"error": "invalid_token"}))
    with pytest.raises(InvalidAuth):
        run(client.status("ha_r"))


def test_too_many_requests_carry_the_wait_time():
    client, _ = api(FakeResponse(429, {"error": "rate_limited"}, {"Retry-After": "12"}))
    with pytest.raises(RateLimited) as err:
        run(client.status("ha_r"))
    assert err.value.retry_after == 12


def test_server_errors_and_network_failures_are_cannot_connect():
    client, _ = api(FakeResponse(500, {}))
    with pytest.raises(CannotConnect):
        run(client.status("ha_r"))
    client, _ = api(error=aiohttp.ClientConnectionError("down"))
    with pytest.raises(CannotConnect):
        run(client.status("ha_r"))
    client, _ = api(error=TimeoutError())
    with pytest.raises(CannotConnect):
        run(client.status("ha_r"))
