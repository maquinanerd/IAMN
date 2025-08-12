import json
import logging
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

                    self.clients[ai_type].append(service_client)
                    logger.info(f"Initialized {ai_type} AI model #{i+1}")
                except Exception as e:
                    logger.error(f"Failed to initialize {ai_type} AI model #{i+1}: {str(e)}")
            if not self.clients[ai_type]:
                logger.warning(f"No valid API keys found or initialized for AI type: {ai_type}")

    def send_prompt(self, prompt: str, category: str) -> str | None:
        """
        Sends a prompt to the appropriate AI model for the given category,
        using a round-robin approach to cycle through available API keys.
        Returns the AI's response as a JSON string, or None on failure.
        """
        ai_type = category

        clients_for_category = self.clients.get(ai_type)
        if not clients_for_category:
            logger.error(f"No AI clients configured or initialized for category: '{ai_type}'")
            return None

        # Round-robin logic
        num_clients = len(clients_for_category)
        client_index = self.client_counters[ai_type] % num_clients
        client = clients_for_category[client_index]
        
        # Increment counter for the next call
        self.client_counters[ai_type] += 1

        ai_name = f"{ai_type}_model_#{client_index + 1}"
        logger.info(f"Attempting to send prompt with {ai_name} (Round-robin index: {client_index})...")

        try:
            request = GenerateContentRequest(
                model="models/gemini-1.5-flash",
                contents=[Content(parts=[Part(text=prompt)])],
                generation_config=GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            response = client.generate_content(request=request)

            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
                logger.info(f"Successfully received response from {ai_name}.")
                self.last_used_times[ai_type] = datetime.now()
                return response_text
            
            logger.warning(f"Empty response from {ai_name}. The model may not have generated content.")
            return None

        except Exception as e:
            logger.error(f"API call to {ai_name} failed: {str(e)}")
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
