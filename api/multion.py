import json
import os
from typing import Any, Dict, List, Optional

import multion  # noqa
from asgiref.sync import sync_to_async  # noqa
from loguru import logger  # noqa
from openai import OpenAI


class MarketplaceAssistant:
    """
    A class to interact with Facebook Marketplace using the Multion API to find deals
    and return structured data.
    """

    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo-0125")
    OPENAI_API_KEY: Optional[str] = os.getenv(
        "OPENAI_API_KEY",
    )
    DATA_LOCATION: Optional[str] = os.getenv("DATA_LOCATION")
    client: OpenAI = OpenAI(api_key=OPENAI_API_KEY)

    def __init__(self) -> None:
        multion.login()
        self.prefix: str = (
            "You are Opal, a personal assistant interacting in a conversation with your human companion to help them find matching products online. The human companion will provide you with a prompt, and you will use the Multion API to browse Facebook Marketplace with the given prompt."
        )

    def parse_input(self, input_str: str) -> str | None:
        if not input_str:
            return ""
        logger.debug(f"Received input string: {input_str}")
        # use the OpenAI API to parse the input string
        response = self.client.chat.completions.create(
            model=self.OPENAI_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON.",
                },
                {
                    "role": "user",
                    "content": f"Parse the following input string into a JSON object with the structure: {{'url': 'URL_PLACEHOLDER', 'errors': ['ERRORS_PLACEHOLDER']}}. Ensure the JSON is well-formed. Input: {input_str}",
                },
            ],
        )
        logger.debug(f"Received response: {response}")
        return response.choices[0].message.content if response.choices else ""

    @sync_to_async
    def filter(self, prompt: str) -> Dict[str, Any]:
        """
        Logs into Multion and uses it to browse Facebook Marketplace with a given prompt.

        :param prompt: The prompt to be used for the Multion API.
        :return: The result of the Multion browsing operation.
        """

        full_prompt = f"{self.prefix} Prompt: {prompt} Using the Human's prompt, Opal will now browse Facebook Marketplace to find matching products. Opal will then provide the human with the marketplace URL with the appropriate filters applied. If you're not able to find a filter, simply move on and make a note in 'errors'. Your result should be in the following format: {{'url': 'URL', 'errors': ['ERRORS']}}"
        logger.debug(f"Using prompt: {full_prompt}")
        response = multion.browse(
            {
                "cmd": full_prompt,
                "url": "https://www.facebook.com/marketplace/sanfrancisco",
                "maxSteps": 25,
            }
        )
        if not response:
            return {"url": "", "errors": ["No results found"]}
        logger.debug(f"Received response: {response}")
        if parsed_input := self.parse_input(response.get("result", "")):
            return json.loads(parsed_input)
        return {"url": "", "errors": ["No results found"]}

    async def message_seller(self, urls: List[str]) -> Any:
        """
        Logs into Multion and uses it to message a seller on Facebook Marketplace.

        :param urls: The list of URLs of the sellers to be messaged.
        :return: The result of the Multion messaging operation.
        """
        full_prompt = f"{self.prefix} For each of the following URLs, Opal will now message the seller with a personalized message on Facebook Marketplace. URLs: {' '.join(urls)}"
        return await sync_to_async(multion.browse)(
            {
                "cmd": full_prompt,
                "url": "https://www.facebook.com/marketplace/sanfrancisco",
                "maxSteps": 100,
            }
        )
