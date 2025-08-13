import os
import logging

# Definição da ordem de execução do pipeline
PIPELINE_ORDER = [
    'screenrant_movies',
    'screenrant_tv',
    'movieweb_movies',
    'collider_movies',
    'collider_tv',
    'cbr_movies',
    'cbr_tv',
    'gamerant_games',
    'thegamer_games',
]

# Configuração dos Feeds RSS, organizados por fontes
RSS_FEEDS = {
    'screenrant_movies': {
        'urls': ['https://screenrant.com/feed/movie-news/'],
        'category': 'movies'
    },
    'screenrant_tv': {
        'urls': ['https://screenrant.com/feed/tv-news/'],
        'category': 'series'
    },
    'movieweb_movies': {
        'urls': ['https://movieweb.com/feed/'],
        'category': 'movies'
    },
    'collider_movies': {
        'urls': ['https://collider.com/feed/category/movie-news/'],
        'category': 'movies'
    },
    'collider_tv': {
        'urls': ['https://collider.com/feed/category/tv-news/'],
        'category': 'series'
    },
    'cbr_movies': {
        'urls': ['https://www.cbr.com/feed/category/movies/news-movies/'],
        'category': 'movies'
    },
    'cbr_tv': {
        'urls': ['https://www.cbr.com/feed/category/tv/news-tv/'],
        'category': 'series'
    },
    'gamerant_games': {
        'urls': ['https://gamerant.com/feed/gaming/'],
        'category': 'games'
    },
    'thegamer_games': {
        'urls': ['https://www.thegamer.com/feed/category/game-news/'],
        'category': 'games'
    }
}

# User Agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# AI Configuration with primary and backup keys.
# The system will always try the first key in the list. If it fails, it will try the next one (backup).
# Removido o '.get()' para falhar explicitamente se as variáveis não estiverem definidas.
# Alterado para os.getenv() para evitar que a aplicação quebre se uma variável de ambiente não estiver definida.
AI_CONFIG = {
    'movies': [
        os.getenv('GEMINI_MOVIES_1'), # Screenrant Movies
        os.getenv('GEMINI_MOVIES_2'), # Movieweb Movies
        os.getenv('GEMINI_MOVIES_3'), # Collider Movies
        os.getenv('GEMINI_MOVIES_4'), # CBR Movies
        os.getenv('GEMINI_BACKUP_1'),
        os.getenv('GEMINI_BACKUP_2'),
    ],
    'series': [
        os.getenv('GEMINI_SERIES_1'), # Screenrant TV
        os.getenv('GEMINI_SERIES_2'), # Collider TV
        os.getenv('GEMINI_SERIES_3'), # CBR TV
        os.getenv('GEMINI_BACKUP_3'),
        os.getenv('GEMINI_BACKUP_4'),
    ],
    'games': [
        os.getenv('GEMINI_GAMES_1'), # GameRant
        os.getenv('GEMINI_GAMES_2'), # TheGamer
        os.getenv('GEMINI_BACKUP_5'),
    ],
}

# WordPress Configuration
WORDPRESS_CONFIG = {
    'url': os.getenv('WORDPRESS_URL'),
    'user': os.getenv('WORDPRESS_USER'),
    'password': os.getenv('WORDPRESS_PASSWORD')
}

# WordPress Categories
WORDPRESS_CATEGORIES = {
    'Notícias': 20,
    'Filmes': 24,
    'Séries': 21,
    'Games': 73,
}

# Schedule Configuration
SCHEDULE_CONFIG = {
    'check_interval': 15,  # minutes
    'max_articles_per_feed': 3,  # Limite de artigos por fonte em cada ciclo
    'api_call_delay': 5, # segundos para aguardar entre o processamento de artigos
    'cleanup_after_hours': 12
}

# Pipeline Configuration
PIPELINE_CONFIG = {
    'images_mode': os.getenv('IMAGES_MODE', 'hotlink'),  # 'hotlink' or 'download_upload'
    'attribution_policy': 'Via {domain}', # Placeholder for attribution text
    'publisher_name': 'Máquina Nerd',
    'publisher_logo_url': 'https://www.maquinanerd.com.br/wp-content/uploads/2023/11/logo-maquina-nerd-400px.png'
}

logger = logging.getLogger(__name__)

def _load_prompt_from_file(file_name: str) -> str:
    """Loads a prompt from the 'prompts' directory, with a fallback to the root directory."""
    base_dir = os.path.dirname(__file__)
    
    # 1. Try the 'prompts' subdirectory
    prompt_path_in_subdir = os.path.join(base_dir, 'prompts', file_name)
    # 2. Fallback to the project root directory
    prompt_path_in_root = os.path.join(base_dir, file_name)

    try:
        with open(prompt_path_in_subdir, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        try:
            with open(prompt_path_in_root, 'r', encoding='utf-8') as f:
                logger.info(f"Prompt file '{file_name}' not found in 'prompts/' directory, using file from project root.")
                return f.read()
        except FileNotFoundError:
            logger.critical(f"CRITICAL ERROR: Prompt file '{file_name}' not found in 'prompts/' or project root directory.")
            return "Error: Prompt file not found."

# Universal Prompt for AI Processing, loaded from an external file
UNIVERSAL_PROMPT = _load_prompt_from_file('universal_prompt.txt')
