import logging
import google.generativeai as genai
from config import AI_CONFIG

logger = logging.getLogger(__name__)

class AIProcessor:
    """
    Manages interactions with the Google Gemini AI models, including a fallback
    mechanism for API keys.
    """
    def __init__(self):
        self.models = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initializes AI models for each category based on the configuration."""
        for category, api_keys in AI_CONFIG.items():
            self.models[category] = []
            for i, key in enumerate(api_keys):
                if key:
                    try:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel('gemini-pro')
                        self.models[category].append(model)
                        logger.info(f"Initialized {category} AI model #{i+1}")
                    except Exception as e:
                        logger.error(f"Failed to initialize {category} AI model #{i+1} with key. Error: {e}")

    def send_prompt(self, prompt: str, category: str) -> str | None:
        """
        Sends a prompt to the appropriate AI model for the given category.
        It will try the primary model first, then fall back to backups if available.
        """
        if category not in self.models or not self.models[category]:
            logger.error(f"No AI models configured or initialized for category: '{category}'")
            return None

        for i, model in enumerate(self.models[category]):
            try:
                logger.info(f"Sending prompt to {category} model #{i+1}...")
                response = model.generate_content(prompt)
                logger.info(f"Successfully received response from {category} model #{i+1}.")
                return response.text
            except Exception as e:
                logger.error(f"Error with {category} model #{i+1}: {e}. Trying next model if available.")
                continue

        logger.error(f"All AI models for category '{category}' failed to process the prompt.")
        return None