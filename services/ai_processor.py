import json
import logging
import re
import time
from datetime import datetime
# Usaremos o cliente de serviço de baixo nível para gerenciar chaves de API individuais
from google.ai.generativelanguage_v1beta.services.generative_service import \
    GenerativeServiceClient
from google.api_core import client_options as client_options_lib
# Tipos necessários para construir a requisição de baixo nível
from google.ai.generativelanguage_v1beta.types import (Content, Part, GenerationConfig, GenerateContentRequest)
from config import AI_CONFIG

logger = logging.getLogger(__name__)

class AIProcessor:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.clients = {}
            self.client_counters = {}
            self.last_used_times = {}
            self._init_clients()
            AIProcessor._initialized = True

    def _init_clients(self):
        """Initialize Gemini models for each AI configuration."""
        for ai_type, api_keys in AI_CONFIG.items():
            self.client_counters[ai_type] = 0
            self.clients[ai_type] = []
            for i, api_key in enumerate(filter(None, api_keys)):  # filter(None, ...) removes empty keys
                try:
                    # Cria um cliente de serviço com sua própria chave de API.
                    # Esta é a abordagem correta para gerenciar múltiplas chaves de forma isolada.
                    client_opts = client_options_lib.ClientOptions(api_key=api_key)
                    service_client = GenerativeServiceClient(client_options=client_opts)

                    self.clients[ai_type].append((service_client, f"...{api_key[-4:]}"))
                    logger.info(f"Initialized {ai_type} AI model #{i+1} (key ending in ...{api_key[-4:]})")
                except Exception as e:
                    logger.error(f"Failed to initialize {ai_type} AI model #{i+1}: {str(e)}")
            if not self.clients[ai_type]:
                logger.warning(f"No valid API keys found or initialized for AI type: {ai_type}")

    def send_prompt(self, prompt: str, category: str) -> str | None:
        """
        Sends a prompt to the appropriate AI model for the given category.
        It uses a round-robin approach to select the starting API key and
        cycles through the rest if the initial one fails.
        Returns the AI's response as a JSON string, or None on failure.
        """
        ai_type = category

        clients_for_category = self.clients.get(ai_type)
        if not clients_for_category:
            logger.error(f"No AI clients configured or initialized for category: '{ai_type}'")
            return None

        num_clients = len(clients_for_category)
        start_index = self.client_counters[ai_type] % num_clients
        
        # Increment counter for the next call to start with a different key
        self.client_counters[ai_type] += 1

        last_error = "Unknown AI processing error."
        # Iterate through clients starting from the round-robin index
        for i in range(num_clients):
            client_index = (start_index + i) % num_clients
            client, partial_key = clients_for_category[client_index]
            ai_name = f"{ai_type}_model_#{client_index + 1}"
            
            logger.info(f"Attempting to send prompt with {ai_name} using key {partial_key} (Attempt {i+1}/{num_clients} for this article)...")

            try:
                request = GenerateContentRequest(
                    model="models/gemini-1.5-flash",
                    contents=[Content(parts=[Part(text=prompt)])],
                    generation_config=GenerationConfig(
                        response_mime_type="application/json"
                    )
                )
                response = client.generate_content(request=request, timeout=60)

                if response.candidates and response.candidates[0].content.parts:
                    response_text = response.candidates[0].content.parts[0].text
                    logger.info(f"Successfully received response from {ai_name}.")
                    self.last_used_times[ai_type] = datetime.now()
                    return response_text
                
                last_error = f"Empty response from {ai_name}"
                logger.warning(f"{last_error}. The model may not have generated content. Trying next model if available.")
                continue

            except Exception as e:
                error_str = str(e)
                last_error = f"API call to {ai_name} failed: {error_str}"

                # Check for rate limit error and respect retry_delay if present
                if "429" in error_str and "exceeded your current quota" in error_str:
                    match = re.search(r"retry_delay {\s*seconds: (\d+)\s*}", error_str)
                    if match:
                        delay = int(match.group(1))
                        # Add a small buffer and cap the delay to avoid excessive waiting
                        sleep_time = min(delay + 2, 60) 
                        logger.warning(f"Rate limit hit for key {partial_key}. Respecting retry_delay and sleeping for {sleep_time} seconds before next attempt.")
                        time.sleep(sleep_time)
                        continue  # Continue to the next key after sleeping
                
                logger.warning(f"{last_error}. Trying next model if available.")
                continue

        logger.error(f"All AI clients for category '{ai_type}' failed. Last error: {last_error}")
        return None

    def get_ai_status(self):
        """Get status of all AIs"""
        status = {}
        for ai_type in AI_CONFIG.keys():
            last_used = self.last_used_times.get(ai_type)
            status[ai_type] = {
                'available_keys': len(self.clients.get(ai_type, [])),
                'last_used': last_used.isoformat() if last_used else "Never"
            }
        return status
