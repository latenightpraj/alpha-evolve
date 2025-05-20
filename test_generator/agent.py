import logging
import asyncio
import re
from typing import Optional, Dict, Any
from litellm import acompletion
from litellm.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError
)

from core.interfaces import TestGeneratorInterface, TestSuite, BaseAgent
from config import settings

logger = logging.getLogger(__name__)

class TestGeneratorAgent(TestGeneratorInterface, BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not settings.PRO_API_KEY:
            raise ValueError("PRO_API_KEY not found in settings. Please set it in your .env file or config.")
        self.model_name = settings.PRO_MODEL
        self.generation_config = {
            "temperature": settings.LITELLM_TEMPERATURE,
            "top_p": settings.LITELLM_TOP_P,
            "top_k": settings.LITELLM_TOP_K,
            "max_tokens": settings.LITELLM_MAX_TOKENS,
            "api_base": settings.PRO_BASE_URL
        }
        logger.info(f"TestGeneratorAgent initialized with model: {self.model_name}")

    async def generate_tests(self, brief: str, model_name: Optional[str] = None, temperature: Optional[float] = None) -> TestSuite:
        effective_model_name = model_name if model_name else self.model_name
        logger.info(f"Attempting to generate tests using model: {effective_model_name}")

        current_generation_config = self.generation_config.copy()
        if temperature is not None:
            current_generation_config["temperature"] = temperature

        retries = settings.API_MAX_RETRIES
        delay = settings.API_RETRY_DELAY_SECONDS

        for attempt in range(retries):
            try:
                logger.debug(f"API Call Attempt {attempt + 1} of {retries} to {effective_model_name}.")
                response = await acompletion(
                    model=effective_model_name,
                    messages=[{"role": "user", "content": brief}],
                    api_key=settings.PRO_API_KEY,
                    **current_generation_config
                )

                if not response.choices:
                    logger.warning("LLM API returned no choices.")
                    return TestSuite(tests_code="", explanation="")

                generated_text = response.choices[0].message.content
                logger.debug(f"Raw response from LLM API:\n--RESPONSE START--\n{generated_text}\n--RESPONSE END--")

                tests_code, explanation = self._split_output(generated_text)
                logger.debug(f"Parsed tests_code length: {len(tests_code)}, explanation length: {len(explanation)}")
                return TestSuite(tests_code=tests_code, explanation=explanation)
            except (APIError, InternalServerError, TimeoutError, RateLimitError, AuthenticationError, BadRequestError) as e:
                logger.warning(f"LLM API error on attempt {attempt + 1}: {type(e).__name__} - {e}. Retrying in {delay}s...")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"LLM API call failed after {retries} retries for model {effective_model_name}.")
                    raise
            except Exception as e:
                logger.error(f"An unexpected error occurred during test generation with {effective_model_name}: {e}", exc_info=True)
                raise

        logger.error(f"Test generation failed for model {effective_model_name} after all retries.")
        return TestSuite(tests_code="", explanation="")

    async def execute(self, brief: str, *args, **kwargs) -> TestSuite:
        return await self.generate_tests(brief, *args, **kwargs)

    def _split_output(self, raw_text: str) -> tuple[str, str]:
        code = ""
        explanation = ""
        match = re.search(r"```(?:python)?\n(.*?)\n```", raw_text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            explanation = re.sub(r"```(?:python)?\n.*?\n```", "", raw_text, count=1, flags=re.DOTALL).strip()
        else:
            code = raw_text.strip()
        return code, explanation
