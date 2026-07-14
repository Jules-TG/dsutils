import time
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, Optional

import requests


def _parse_retry_after(response: requests.Response) -> int:
    """
    Extracts the relative delay in seconds from standard rate limit headers.

    This function prioritises the RFC 7231 standard ``Retry-After`` header. If
    absent, it falls back to checking common absolute timestamp headers,
    accounting for potential server-to-client clock drift by using the remote
    server's ``Date`` header as the baseline.

    Args:
        response: The response object from the HTTP request.

    Returns:
        An integer representing the number of seconds to pause execution. Returns
        0 if no valid rate limit header is found.
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass

    reset_timestamp = response.headers.get("X-RateLimit-Reset") or response.headers.get(
        "x-ratelimit-reset"
    )
    if reset_timestamp:
        try:
            remote_time_str = response.headers.get("Date")
            if remote_time_str:
                remote_time = parsedate_to_datetime(remote_time_str).timestamp()
            else:
                remote_time = time.time()

            return max(int(float(reset_timestamp) - remote_time), 1) + 1
        except ValueError, TypeError:
            pass

    return 0


def send_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    max_retries: int = 5,
    initial_backoff: float = 2.0,
    timeout: float = 30.0,
    payload_error_handler: Optional[
        Callable[[requests.Response], Optional[int]]
    ] = None,
) -> requests.Response:
    """Sends an HTTP request with adaptive retry logic for errors and rate limits.

    Handles transient gateway errors (502, 503, 504) via exponential backoff.
    Handles rate limits (429, 403) by parsing standard headers via relative
    delay calculations. An optional callback can be supplied to parse API-specific
    error payloads wrapped inside HTTP 200 responses.

    Args:
        method: The HTTP method to use (e.g., 'GET', 'POST').
        url: The target URL for the request.
        headers: Dictionary of HTTP headers to send.
        params: Dictionary of URL parameters.
        json_data: Dictionary representing the JSON body payload.
        max_retries: Maximum number of retry attempts allowed before raising.
        initial_backoff: Starting delay in seconds for transient server errors.
        timeout: Maximum time in seconds to wait for a server response.
        payload_error_handler: Optional callable that inspects an HTTP 200
            response payload and returns a sleep duration in seconds if an
            internal rate limit is detected, or None otherwise.

    Returns:
        The successful requests.Response object.

    Raises:
        requests.exceptions.RequestException: If the network error persists past
            the maximum retry threshold or if an unhandled status code occurs.
    """
    current_backoff = initial_backoff

    for attempt in range(max_retries):
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=timeout,
            )

            if response.status_code in [502, 503, 504]:
                if attempt == max_retries - 1:
                    return response
                print(
                    f"Gateway Error {response.status_code}. "
                    f"Retrying in {current_backoff}s..."
                )
                time.sleep(current_backoff)
                current_backoff *= 2
                continue

            if response.status_code in [403, 429]:
                sleep_duration = _parse_retry_after(response)
                if sleep_duration == 0:
                    sleep_duration = current_backoff
                    current_backoff *= 2

                print(
                    f"Rate limit hit ({response.status_code}). "
                    f"Sleeping for {sleep_duration}s..."
                )
                time.sleep(sleep_duration)
                continue

            if response.status_code == 200 and payload_error_handler:
                sleep_duration = payload_error_handler(response)
                if sleep_duration:
                    print(
                        "Internal payload rate limit hit. "
                        f"Sleeping for {sleep_duration}s..."
                    )
                    time.sleep(sleep_duration)
                    continue

            return response

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Network error: {e}. Retrying in {current_backoff}s...")
            time.sleep(current_backoff)
            current_backoff *= 2

    return response
