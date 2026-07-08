import warnings
from typing import Type

from openai import OpenAI
from pydantic import BaseModel


def get_openai_client(base_url: str, openai_token: str, max_retries: int = 5) -> OpenAI:
    """Initialise and return a synchronous OpenAI client.

    Args:
        base_url: The endpoint URL.
        openai_token: The API key or token for authentication.
        max_retries: Maximum number of retry attempts for failed
            requests.

    Returns:
        A configured ``OpenAI`` client instance.
    """
    return OpenAI(base_url=base_url, api_key=openai_token, max_retries=max_retries)


def get_token_cost(token_count: int, token_type: str, model: str) -> float:
    """Calculate the estimated USD cost for a given token usage.

    Actual costs may be lower if the input is cached.

    Args:
        token_count: The number of tokens consumed.
        token_type: Whether the tokens are ``input`` or ``output``.
        model: The model name to look up pricing for.

    Returns:
        The estimated cost in US dollars.

    Raises:
        ValueError: If ``token_type`` is not ``input`` or ``output``, or
            if the model is not found in the price table.
    """
    if token_type not in ["input", "output"]:
        raise ValueError(
            f"Invalid token_type: {token_type}. This should be 'input' or 'output'"
        )

    # Prices in USD
    # TODO - Implement more complete and robust pricing
    prices = {"gpt-5.4-nano": {"input": 0.2, "output": 1.25}}

    model_prices = prices.get(model)

    cost_per_m = model_prices[token_type]

    return (token_count * cost_per_m) / 1_000_000


def request_openai_response(
    client: OpenAI,
    model: str,
    max_tokens: int,
    system_content: str,
    user_content: str,
    reasoning_effort: str | None = None,
    temperature: float | None = None,
    response_format: Type[BaseModel] | None = None,
    estimate_cost: bool = False,
) -> str | BaseModel | tuple[str, float] | tuple[BaseModel, float]:
    """Send a chat completion request and return the response content.

    Supports optional structured output via a Pydantic ``response_format``,
    configurable reasoning effort, and temperature control.

    Args:
        client: An ``OpenAI`` client instance.
        model: The model identifier to use.
        max_tokens: Maximum completion tokens for the response.
        system_content: The system prompt content.
        user_content: The user prompt content.
        reasoning_effort: The reasoning effort level (``none``, ``minimal``,
            ``low``, ``medium``, ``high``, ``xhigh``).
        temperature: The sampling temperature, between 0 and 2.
        response_format: A Pydantic ``BaseModel`` subclass for structured
            output.
        estimate_cost: If ``True``, return the estimated cost alongside the
            result.

    Returns:
        The message as a string (or ``BaseModel`` instance if ``response_format`` is set). When ``estimate_cost`` is ``True``, returns a ``(result, cost)`` tuple.

    Raises:
        ValueError: If ``temperature`` is outside the range [0, 2] or
            ``reasoning_effort`` is not a valid value.
        UserWarning: If the response was truncated due to hitting
            ``max_tokens``.
    """  # noqa: E501
    if temperature is not None and not (0.0 <= temperature <= 2.0):
        raise ValueError(f"Invalid temperature: {temperature}, must be between 0 and 2")

    if reasoning_effort not in ["none", "minimal", "low", "medium", "high", "xhigh"]:
        raise ValueError(f"Invalid reasoning effort: {reasoning_effort}")

    args = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "max_completion_tokens": max_tokens,
    }

    if temperature:
        args["temperature"] = temperature

    if reasoning_effort:
        args["reasoning_effort"] = reasoning_effort

    if response_format:
        args["response_format"] = response_format

        response = client.beta.chat.completions.parse(**args)

    else:
        response = client.beta.chat.completions.create(**args)

    message = response.choices[0].message

    result = message.parsed if response_format else message.content

    usage = response.usage

    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens

    if response.choices[0].finish_reason == "length":
        warnings.warn("Max output tokens exceeded!", UserWarning)

    estimated_cost = get_token_cost(input_tokens, "input", model) + get_token_cost(
        output_tokens, "output", model
    )

    if estimate_cost:
        return result, estimated_cost

    else:
        return result
