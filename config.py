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

# AI Configuration with primary and backup keys.
# The system will always try the first key in the list. If it fails, it will try the next one (backup).
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

# Pipeline Configuration
PIPELINE_CONFIG = {
    'images_mode': os.getenv('IMAGES_MODE', 'hotlink'),  # 'hotlink' or 'download_upload'
    'attribution_policy': 'Via {domain}', # Placeholder for attribution text
    'publisher_name': 'Máquina Nerd',
    'publisher_logo_url': 'https://www.maquinanerd.com.br/wp-content/uploads/2023/11/logo-maquina-nerd-400px.png'
}

# Universal Prompt for AI Processing
UNIVERSAL_PROMPT = """
Você é um jornalista digital especializado em cultura pop, cinema e séries, com experiência em otimização para Google News e SEO técnico. Sua tarefa é revisar e otimizar o conteúdo abaixo sem alterar o sentido original, aprimorando sua estrutura, legibilidade e potencial de ranqueamento.

✅ Diretrizes obrigatórias para otimização:

**Título:**
- Reescreva o título original tornando-o mais atrativo e claro.
- Inclua palavras-chave relevantes para melhorar o SEO.
- Mantenha foco no tema, sem clickbait exagerado.
- ⚠️ IMPORTANTE: O título deve ser APENAS TEXTO PURO, sem HTML, tags ou formatação.
- Não use <b>, <a>, <i>, <span> ou qualquer tag HTML no título.
- O título será usado em meta tags, RSS feeds e Google News onde HTML causa erros.

**Resumo (Excerpt):**
- Reescreva o resumo para ser mais chamativo e informativo.
- Foque em engajamento e performance nos resultados do Google News.

**Conteúdo:**
- Reestruture os parágrafos longos em blocos mais curtos e escaneáveis.
- **Não resuma ou encurte o texto.** O objetivo é reestruturar e otimizar, mantendo toda a informação original. Apenas melhore a fluidez e a formatação.
- ⚠️ IMPORTANTE: Envolva cada parágrafo individualmente com a tag HTML <p>. Exemplo: <p>Primeiro parágrafo.</p><p>Segundo parágrafo.</p>
- Não use <br> para criar parágrafos.
- Mantenha o tom jornalístico e objetivo.
- Não altere o sentido da informação.

**Negrito:**
- Destaque os termos mais relevantes usando apenas a tag HTML <b>.
- Ex: nomes de filmes, personagens, diretores, plataformas, datas, eventos.

**Links internos:**
- Baseando-se nas tags fornecidas, insira links internos usando a estrutura:
  <a href="{domain}/tag/NOME-DA-TAG">Texto âncora</a>
- Quando possível, aplique negrito combinado com link:
  <b><a href="{domain}/tag/stranger-things">Stranger Things</a></b>

⚠️ **Regras Técnicas:**
- Use somente HTML puro: <b>, <a>.
- Não utilize Markdown (**texto** ou [link](url)).
- Não adicione informações novas que não estejam no texto original ou na mídia fornecida.
- Utilize o conteúdo do campo Tags para decidir onde inserir links internos relevantes.

🔽 **DADOS DISPONÍVEIS PARA OTIMIZAÇÃO**

**Conteúdo original:**

**Título:** {title}

**Resumo (se disponível):** {excerpt}

**Conteúdo:**
{content}

📤 **FORMATO DA RESPOSTA (obrigatório)**
Responda APENAS em JSON no seguinte formato:

{{
  "titulo_final": "...",
  "conteudo_final": "<p>...</p><p>...</p>",
  "meta_description": "...",
  "focus_keyword": "...",
  "categoria": "...",
  "obra_principal": "...",
  "tags": ["...", "...", "..."],
  "imagens": ["url1", "url2", "..."],
  "youtube_links": ["link1", "link2", "..."],
  "twitter_links": ["link1", "link2", "..."],
  "threads_links": ["link1", "link2", "..."]
}}
"""
