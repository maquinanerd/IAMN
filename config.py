import os

# RSS Feeds Configuration
RSS_FEEDS = {
    # Movies Feeds
    'movies_screenrant': 'https://screenrant.com/feed/movie-news/',
    'movies_movieweb': 'https://movieweb.com/movie-news/',
    'movies_collider': 'https://collider.com/movie-news/',
    'movies_cbr': 'https://www.cbr.com/category/movies/news-movies/',
    # TV Shows Feeds
    'series_screenrant': 'https://screenrant.com/feed/tv-news/',
    'series_movieweb': 'https://movieweb.com/feed/tv-news/',
    'series_collider': 'https://collider.com/feed/category/tv-news/',
    'series_cbr': 'https://www.cbr.com/feed/category/tv/news-tv/',
    # Games Feeds
    'games_gamerant': 'https://gamerant.com/feed/gaming/',
    'games_thegamer': 'https://www.thegamer.com/feed/category/game-news/',
}

# User Agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# AI Configuration with multiple keys for redundancy
AI_CONFIG = {
    'movies': [
        os.getenv('GEMINI_MOVIES_1'),
        os.getenv('GEMINI_MOVIES_2'),
        os.getenv('GEMINI_MOVIES_3'),
    ],
    'series': [
        os.getenv('GEMINI_SERIES_1'),
        os.getenv('GEMINI_SERIES_2'),
        os.getenv('GEMINI_SERIES_3'),
    ],
    'games': [
        os.getenv('GEMINI_GAMES_1'),
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
    'max_articles_per_run': 5,  # aumentado para processar mais artigos
    'cleanup_after_hours': 12
}

# Universal Prompt for AI Processing
UNIVERSAL_PROMPT = """
Você é um redator especialista em cultura pop. Reescreva o seguinte artigo em português com SEO, parágrafos bem separados e otimize para o Google.

REGRAS:
1. Traduza o artigo original para o português, mantendo todos os detalhes e a estrutura.
2. Reescreva com pelo menos 5-7 parágrafos separados (com quebras duplas).
3. Crie um título otimizado para SEO.
4. Crie uma meta description de até 150 caracteres.
5. Destaque a palavra-chave principal.
6. Categorize o artigo como 'Filmes', 'Séries' ou 'Notícias'.
7. Identifique o nome do filme ou série principal abordado no artigo.
8. Se houver embeds de vídeos do YouTube ou publicações do Twitter, incorpore diretamente no local apropriado do conteúdo com o código embed real.
9. Mantenha a coerência e a naturalidade do texto, como em uma publicação profissional de jornalismo de entretenimento.

ARTIGO ORIGINAL:
Título: {titulo}
Conteúdo: {conteudo}

Responda APENAS em JSON:
{{
  "titulo_final": "...",
  "conteudo_final": "...",
  "meta_description": "...",
  "focus_keyword": "...",
  "categoria": "...",
  "obra_principal": "...",
  "tags": ["...", "...", "..."]
}}
"""
