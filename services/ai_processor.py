import json
import logging
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
            self._init_clients()
            AIProcessor._initialized = True

    def _init_clients(self):
        """Initialize Gemini models for each AI configuration."""
        for ai_type, api_keys in AI_CONFIG.items():
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
        Envia um prompt para o modelo de IA apropriado para a categoria fornecida.
        Tenta o modelo primário primeiro, depois recorre aos backups, se disponíveis.
        Retorna a resposta da IA como uma string JSON ou None em caso de falha.
        """
        ai_type = category  # O agendador passa a categoria (ex: 'movies') que mapeia para o tipo de IA.

        if not self.clients.get(ai_type):
            logger.error(f"Nenhum cliente de IA configurado ou inicializado para a categoria: '{ai_type}'")
            return None

        last_error = "Erro desconhecido no processamento da IA."
        for i, client in enumerate(self.clients[ai_type]):
            ai_name = f"{ai_type}_model_#{i+1}"
            logger.info(f"Tentando enviar prompt com {ai_name}...")

            try:
                # Constrói a requisição para o GenerativeServiceClient
                request = GenerateContentRequest(
                    model="models/gemini-1.5-flash",  # O nome completo do modelo é necessário aqui
                    contents=[Content(parts=[Part(text=prompt)])],
                    generation_config=GenerationConfig(
                        response_mime_type="application/json"
                    )
                )
                response = client.generate_content(request=request)

                if response.candidates and response.candidates[0].content.parts:
                    response_text = response.candidates[0].content.parts[0].text
                    logger.info(f"Resposta recebida com sucesso de {ai_name}.")
                    return response_text
                else:
                    last_error = f"Resposta vazia de {ai_name}"
                    logger.warning(f"{last_error}. Tentando próximo modelo, se disponível.")
                    continue

            except Exception as e:
                last_error = f"Chamada de API para {ai_name} falhou: {str(e)}"
                logger.warning(f"{last_error}. Tentando próximo modelo, se disponível.")
                continue

        logger.error(f"Todos os clientes de IA para a categoria '{ai_type}' falharam. Último erro: {last_error}")
        return None

    def get_ai_status(self):
        """Get status of all AIs"""
        status = {}
        for ai_type in AI_CONFIG.keys():
            status[ai_type] = {
                'available_keys': len(self.clients.get(ai_type, [])),
                'last_used': self._get_last_used_time(ai_type)
            }
        return status
