import logging
import feedparser
from models import Article
from dto import ExtractedArticleDTO
from extensions import db

logger = logging.getLogger(__name__)

class RSSMonitor:
    def fetch_new_articles(self, feed_key: str, urls: list, limit: int) -> list[ExtractedArticleDTO]:
        """
        Busca novos artigos de uma lista de URLs de feed RSS para uma chave de feed específica,
        evitando duplicatas que já existem no banco de dados.

        Args:
            feed_key: A chave identificadora do feed (ex: 'screenrant_filmes_tv').
            urls: Uma lista de URLs de feed RSS para verificar.
            limit: O número máximo de novos artigos a serem retornados.

        Returns:
            Uma lista de objetos ExtractedArticleDTO para os novos artigos encontrados.
        """
        logger.info(f"[{feed_key}] Verificando novos artigos em {len(urls)} URL(s).")
        new_articles_to_process = []

        # Obtém todas as URLs de origem existentes do banco de dados para verificar duplicatas de forma eficiente.
        # Usar um `set` para a verificação é muito mais rápido (O(1) em média).
        # A consulta retorna uma lista de tuplas de um elemento, ex: [('url1',), ('url2',)].
        # A sintaxe {url for (url,) in ...} desempacota cada tupla para extrair a string da URL.
        existing_urls = {url for (url,) in db.session.query(Article.source_url).all()}

        for url in urls:
            if len(new_articles_to_process) >= limit:
                logger.info(f"[{feed_key}] Limite de {limit} artigos atingido. Parando a busca.")
                break

            try:
                feed = feedparser.parse(url)
                if feed.bozo:
                    # bozo é True se o feed não estiver bem formatado
                    bozo_exception = feed.get("bozo_exception", "erro desconhecido")
                    logger.warning(f"[{feed_key}] Feed mal formatado em {url}. Motivo: {bozo_exception}")
                    continue

                for entry in feed.entries:
                    if len(new_articles_to_process) >= limit:
                        break

                    article_url = entry.get("link")
                    if not article_url:
                        logger.warning(f"[{feed_key}] Entrada do feed sem 'link'. Título: {entry.get('title', 'N/A')}")
                        continue

                    if article_url not in existing_urls:
                        logger.info(f"[{feed_key}] Novo artigo encontrado: {entry.get('title', article_url)}")
                        # Cria um DTO com a URL de origem para a próxima etapa de processamento
                        dto = ExtractedArticleDTO(source_url=article_url)
                        new_articles_to_process.append(dto)
                        existing_urls.add(article_url)  # Adiciona ao set para evitar duplicatas na mesma execução

            except Exception as e:
                logger.error(f"[{feed_key}] Falha ao processar o feed RSS em {url}. Erro: {e}", exc_info=True)

        # Garante que não excedemos o limite, caso o último feed tenha muitos artigos novos.
        return new_articles_to_process[:limit]

    def cleanup_old_articles(self):
        """Executa a limpeza de artigos antigos no banco de dados."""
        logger.info("Executando limpeza de artigos antigos...")
        # A lógica de limpeza real pode ser adicionada aqui, como remover artigos com falha há mais de X dias.
        pass
