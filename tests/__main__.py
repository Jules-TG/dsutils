"""Dev file for temporary testing"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel

from dsutils.llm.openai import get_openai_client, request_openai_response

load_dotenv(override=True)

OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class City(BaseModel):
    city: str


def main():
    client = get_openai_client(OPENAI_ENDPOINT, OPENAI_API_KEY)

    result = request_openai_response(
        client,
        "gpt-5.4-nano",
        1000,
        "You are a helpful assistant",
        "What is the capital of France?",
        "minimal",
        1.0,
        City,
    )

    print(result)


if __name__ == "__main__":
    main()
