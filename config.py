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

# Universal Prompt for AI Processing
UNIVERSAL_PROMPT = """
Você é um jornalista digital especializado em cultura pop, cinema e séries, com experiência em otimização para Google News, SEO técnico e Yoast SEO (score 100). Sua tarefa é revisar, traduzir (se necessário) e otimizar o conteúdo abaixo sem alterar o sentido original, aprimorando sua estrutura, legibilidade e potencial de ranqueamento no Google.

✅ **Diretrizes obrigatórias:**

**Título:**
- Reescreva o título original tornando-o mais atrativo e claro.
- Inclua palavras-chave relevantes para melhorar o SEO.
- Não use HTML no título. Apenas texto puro.
- Mantenha foco no tema, sem clickbait exagerado.

**Resumo (Excerpt / Meta Description):**
- Crie uma meta description de até 150 caracteres, chamativa e objetiva.
- Deve incluir a palavra-chave principal.
- Otimizada para CTR no Google News e buscas.

**Conteúdo:**
- Traduza para português, se necessário, mantendo todos os detalhes originais.
- Não resuma nem corte informações.
- Reestruture parágrafos longos em blocos curtos e escaneáveis.
- Envolva cada parágrafo individualmente com a tag <p> (sem <br>).
- Mantenha tom jornalístico e natural.
- Destaque termos relevantes com <b>.
- Insira links internos baseados nas tags fornecidas:
  <a href="{inp.domain}/tag/NOME-DA-TAG">Texto âncora</a>
- Quando possível, combine negrito com link: <b><a href="{inp.domain}/tag/exemplo">Exemplo</a></b>.
- Se houver vídeos do YouTube, publicações do Twitter/X ou Threads, incorpore usando o código embed real.
- Categorize como "Filmes", "Séries" ou "Notícias".
- Identifique o nome da obra principal abordada.
- Garanta pontuação máxima no Yoast SEO, usando palavra-chave no título, meta description, primeiro parágrafo, subtítulos e conclusão.

**Extração de Mídia:**
- Analise o conteúdo original e extraia:
  - Lista de URLs de imagens (src original).
  - Lista de links do YouTube (vídeos).
  - Lista de links do Twitter/X.
  - Lista de links do Threads.
- Retorne essas listas no JSON separadas por tipo.

**Negrito:**
- Use apenas <b> para destacar termos relevantes (filmes, séries, diretores, plataformas, datas, eventos).

**Regras técnicas:**
- Apenas HTML puro: <p>, <b>, <a>.
- Não use Markdown.
- Não invente informações que não estejam no texto original.

🔽 **DADOS DISPONÍVEIS PARA OTIMIZAÇÃO**

**Título Original:** {titulo}
**Conteúdo Original:**
{conteudo}

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
