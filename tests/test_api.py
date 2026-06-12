from unittest.mock import MagicMock, patch

import pytest
import requests

from dsutils.api.client import send_request


@patch("dsutils.api.client.requests.request")
def test_send_request_success(mock_request):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    response = send_request(method="GET", url="https://example.com")

    assert response.status_code == 200
    mock_request.assert_called_once_with(
        method="GET",
        url="https://example.com",
        headers=None,
        params=None,
        json=None,
        timeout=30.0,
    )


@patch("dsutils.api.client.requests.request")
def test_send_request_method_standardisation(mock_request):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    send_request(method="get", url="https://example.com")

    mock_request.assert_called_once_with(
        method="GET",
        url="https://example.com",
        headers=None,
        params=None,
        json=None,
        timeout=30.0,
    )


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_gateway_error_retry_and_success(mock_request, mock_sleep):
    mock_response_502 = MagicMock(spec=requests.Response)
    mock_response_502.status_code = 502
    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200

    mock_request.side_effect = [mock_response_502, mock_response_200]

    response = send_request(
        method="GET", url="https://example.com", initial_backoff=2.0
    )

    assert response.status_code == 200
    assert mock_request.call_count == 2
    mock_sleep.assert_called_once_with(2.0)


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_gateway_error_max_retries(mock_request, mock_sleep):
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 503
    mock_request.return_value = mock_response

    response = send_request(
        method="POST", url="https://example.com", max_retries=3, initial_backoff=1.0
    )

    assert response.status_code == 503
    assert mock_request.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)
    mock_sleep.assert_any_call(2.0)


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_rate_limit_retry_after(mock_request, mock_sleep):
    mock_response_429 = MagicMock(spec=requests.Response)
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "5"}

    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200

    mock_request.side_effect = [mock_response_429, mock_response_200]

    response = send_request(method="GET", url="https://example.com")

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(5)


@patch("dsutils.api.client.parsedate_to_datetime")
@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_rate_limit_x_ratelimit_reset(
    mock_request, mock_sleep, mock_parsedate
):
    mock_response_403 = MagicMock(spec=requests.Response)
    mock_response_403.status_code = 403
    mock_response_403.headers = {
        "X-RateLimit-Reset": "1000.0",
        "Date": "Fri, 22 May 2026 14:14:50 GMT",
    }

    mock_datetime = MagicMock()
    mock_datetime.timestamp.return_value = 990.0
    mock_parsedate.return_value = mock_datetime

    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200

    mock_request.side_effect = [mock_response_403, mock_response_200]

    response = send_request(method="GET", url="https://example.com")

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(11)


@patch("dsutils.api.client.time.time")
@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_rate_limit_x_ratelimit_no_date(
    mock_request, mock_sleep, mock_time
):
    mock_response_429 = MagicMock(spec=requests.Response)
    mock_response_429.status_code = 429
    mock_response_429.headers = {"X-RateLimit-Reset": "1000.0"}

    mock_time.return_value = 990.0

    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200

    mock_request.side_effect = [mock_response_429, mock_response_200]

    response = send_request(method="GET", url="https://example.com")

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(11)


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_rate_limit_invalid_headers(mock_request, mock_sleep):
    mock_response_429 = MagicMock(spec=requests.Response)
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "invalid_int"}

    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200

    mock_request.side_effect = [mock_response_429, mock_response_200]

    response = send_request(
        method="GET", url="https://example.com", initial_backoff=2.0
    )

    assert response.status_code == 200
    mock_sleep.assert_called_once_with(2.0)


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_payload_error_handler(mock_request, mock_sleep):
    mock_response_200_error = MagicMock(spec=requests.Response)
    mock_response_200_error.status_code = 200
    mock_response_200_success = MagicMock(spec=requests.Response)
    mock_response_200_success.status_code = 200

    mock_request.side_effect = [mock_response_200_error, mock_response_200_success]

    handler = MagicMock(side_effect=[4, None])

    response = send_request(
        method="GET", url="https://example.com", payload_error_handler=handler
    )

    assert response.status_code == 200
    assert mock_request.call_count == 2
    assert handler.call_count == 2
    mock_sleep.assert_called_once_with(4)


@patch("dsutils.api.client.time.sleep")
@patch("dsutils.api.client.requests.request")
def test_send_request_network_exception_retry_and_raise(mock_request, mock_sleep):
    mock_request.side_effect = requests.exceptions.ConnectionError("Connection refused")

    with pytest.raises(requests.exceptions.RequestException):
        send_request(
            method="GET", url="https://example.com", max_retries=2, initial_backoff=2.0
        )

    assert mock_request.call_count == 2
    mock_sleep.assert_called_once_with(2.0)
