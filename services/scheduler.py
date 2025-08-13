import logging
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import re
import unicodedata
from pytz import timezone
from urllib.parse import urlparse
from services.rss_monitor import RSSMonitor
from services.ai_processor import AIProcessor
from services.wordpress_publisher import WordPressPublisher
from services.content_extractor import ContentExtractor
from services.schema_generator import SchemaGenerator
from models import Article
from extensions import db
from dto import PublishedArticleDTO, FeaturedImageDTO, ExtractedArticleDTO
from config import SCHEDULE_CONFIG, PIPELINE_CONFIG, UNIVERSAL_PROMPT, WORDPRESS_CONFIG, PIPELINE_ORDER, RSS_FEEDS

logger = logging.getLogger(__name__)

# Reduz o ruído de logs do APScheduler durante o desenvolvimento
logging.getLogger('apscheduler').setLevel(logging.WARNING)

def slugify(value: str) -> str:
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens. Handles unicode characters.
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

class ContentAutomationScheduler:
    def __init__(self):
        # Padroniza o timezone para evitar ambiguidades com jobs baseados em horário (cron)
        self.scheduler = BackgroundScheduler(timezone=timezone("America/Sao_Paulo"))

        # Configuração opcional de persistência de jobs no banco de dados.
        # Útil para ambientes de produção, para que os jobs não se percam se a aplicação reiniciar.
        # Ative definindo a variável de ambiente ENABLE_JOBSTORE_SQLALCHEMY="1"
        if os.getenv("ENABLE_JOBSTORE_SQLALCHEMY", "0") == "1":
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
            # Usa um banco de dados SQLite por padrão para a persistência, mas pode ser alterado
            # via variável de ambiente para usar o mesmo banco de dados da aplicação.
            db_url = os.getenv("SCHEDULER_DB_URL", "sqlite:///scheduler_jobs.db")
            jobstores = {
                "default": SQLAlchemyJobStore(url=db_url)
            }
            self.scheduler.configure(jobstores=jobstores)
            logger.info(f"Scheduler persistence enabled using SQLAlchemyJobStore at {db_url}")

        self.rss_monitor = RSSMonitor()
        self.ai_processor = AIProcessor()
        self.content_extractor = ContentExtractor()
        self.schema_generator = SchemaGenerator()
        self.wordpress_publisher = WordPressPublisher()
        self.is_running = False

    def start(self):
        """Start the automation scheduler"""
        if not self.is_running:
            # Adiciona um job para executar o ciclo imediatamente na inicialização.
            # Este job roda apenas uma vez.
            self.scheduler.add_job(
                func=self.automation_cycle,
                trigger='date',
                id='content_automation_initial_run',
                name='Content Automation Initial Run'
            )

            # Adiciona o job principal de automação de conteúdo.
            # id: Identificador único para evitar duplicação.
            # replace_existing=True: Garante que, se um job com o mesmo ID já existir, ele será substituído.
            # coalesce=True: Se várias execuções estiverem pendentes (ex: após a app ficar offline), agrupa em uma só.
            # max_instances=1: Garante que apenas uma instância deste job rode por vez.
            # misfire_grace_time: Tolerância em segundos para executar um job que perdeu seu horário.
            self.scheduler.add_job(
                func=self.automation_cycle,
                trigger='interval',
                minutes=SCHEDULE_CONFIG.get('check_interval', 15),
                id='content_automation_cycle',
                name='Content Automation Cycle',
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=120
            )

            # Adiciona o job de limpeza do banco de dados para rodar diariamente à meia-noite.
            self.scheduler.add_job(
                func=self.cleanup_cycle,
                trigger='cron',
                hour='0',
                minute='0',
                id='database_cleanup',
                name='Database Cleanup',
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=300
            )

            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started with timezone: {self.scheduler.timezone}")

    def stop(self):
        """Stop the automation scheduler"""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Content automation scheduler stopped")

    def automation_cycle(self, limit: int = None):
        """
        Main automation cycle. Fetches, processes, and prepares articles for publishing.
        Processes feeds sequentially based on the order defined in PIPELINE_ORDER.
        """
        with self.app.app_context():
            try:
                logger.info("=== Starting automation cycle ===")
                
                # Fetch all existing URLs ONCE at the beginning of the cycle for efficiency.
                all_known_urls = {article.source_url for article in Article.query.with_entities(Article.source_url).all()}
                logger.info(f"Initialized with {len(all_known_urls)} known URLs from the database.")

                # Processa os feeds na ordem definida em PIPELINE_ORDER
                for feed_key in PIPELINE_ORDER:
                    if feed_key not in RSS_FEEDS:
                        logger.warning(f"Feed key '{feed_key}' from PIPELINE_ORDER not found in RSS_FEEDS. Skipping.")
                        continue

                    feed_config = RSS_FEEDS[feed_key]
                    category = feed_config.get('category')
                    if not category:
                        logger.warning(f"Feed '{feed_key}' has no category defined. Skipping.")
                        continue
                    
                    logger.info(f"--- Starting processing for feed: {feed_key} (Category: {category}) ---")

                    # Step 1: Fetch new articles for the current feed
                    articles_to_process = self.rss_monitor.fetch_new_articles(
                        feed_key=feed_key,
                        urls=feed_config['urls'],
                        limit=SCHEDULE_CONFIG.get('max_articles_per_feed', 3),
                        existing_urls=all_known_urls
                    )
                    logger.info(f"Found {len(articles_to_process)} new articles from {feed_key}.")

                    if not articles_to_process:
                        logger.info(f"--- No new articles for feed: {feed_key}. Moving to next. ---")
                        continue

                    for article_data in articles_to_process:
                        self.process_single_article(article_data, category, feed_key)
                        # Adiciona uma pausa para evitar atingir os limites de taxa da API por minuto.
                        delay = SCHEDULE_CONFIG.get('api_call_delay', 20)
                        logger.debug(f"Aguardando {delay} segundos antes do próximo artigo...")
                        time.sleep(delay)
                    
                    logger.info(f"--- Finished processing for feed: {feed_key} ---")

                logger.info("=== Automation cycle completed. ===")

            except Exception as e:
                logger.error(f"Error in automation cycle: {str(e)}", exc_info=True)

    def process_single_article(self, article_dto: ExtractedArticleDTO, category: str, feed_key: str):
        """Processes a single article from extraction to publishing readiness."""
        source_url = article_dto.source_url
        logger.info(f"--- Processing URL: {source_url} ---")

        # Step 2: Extract and sanitize content
        extracted_data = self.content_extractor.extract(source_url)
        if not extracted_data:
            logger.error(f"Extraction failed for {source_url}, skipping.")
            return

        # Step 3: Rewrite with AI
        wp_url = WORDPRESS_CONFIG.get('url', '')
        parsed_url = urlparse(wp_url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}" if wp_url else ""
        
        # Acessa os metadados corretamente dentro do dicionário aninhado
        metadata = extracted_data.get('metadata', {})

        prompt = UNIVERSAL_PROMPT.format(
            title=metadata.get('title') or "Sem título",
            excerpt=metadata.get('summary') or "Sem resumo",
            domain=domain,
            content=extracted_data.get('content_html')
        )
        ai_result_json = self.ai_processor.send_prompt(prompt, category=category)

        if not ai_result_json:
            logger.error(f"AI processing failed for {source_url}. Skipping article.")
            return
        
        try:
            ai_result = json.loads(ai_result_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from AI for {source_url}. Response was: {ai_result_json[:200]}...")
            return

        # Step 4: Generate Schema.org
        schema_ld = self.schema_generator.generate_news_article_schema(
            headline=ai_result['titulo_final'],
            summary=ai_result['meta_description'],
            image_url=metadata.get('featured_image'),
            canonical_url=metadata.get('canonical_url'),
            date_published=metadata.get('published_time'),
            author_name=metadata.get('author'),
            publisher_name=PIPELINE_CONFIG['publisher_name'],
            publisher_logo_url=PIPELINE_CONFIG['publisher_logo_url']
        )

        # Step 5: Assemble the final DTO
        final_dto = PublishedArticleDTO(
            source_url=source_url,
            canonical_url=metadata.get('canonical_url'),
            title=ai_result['titulo_final'],
            summary=ai_result['meta_description'],
            slug=slugify(ai_result['titulo_final']),
            featured_image=FeaturedImageDTO(url=metadata.get('featured_image'), alt=ai_result['titulo_final']),
            content_html=ai_result['conteudo_final'],
            tags=ai_result['tags'],
            category=ai_result['categoria'],
            schema_json_ld=schema_ld,
            attribution=PIPELINE_CONFIG['attribution_policy'].format(domain=urlparse(source_url).netloc)
        )

        # Step 6: Persist the article to the database to prevent reprocessing.
        # This is crucial for the rss_monitor to know which articles have been seen.
        try:
            # NOTE: Field names are inferred from context. Adjust if your Article model is different.
            new_article = Article(
                source_url=source_url,
                original_title=metadata.get('title', 'N/A'),
                titulo_final=final_dto.title,
                meta_description=final_dto.summary,
                conteudo_final=final_dto.content_html,
                slug=final_dto.slug,
                tags=json.dumps(final_dto.tags, ensure_ascii=False),
                categoria=ai_result.get('categoria'),
                obra_principal=ai_result.get('obra_principal'),
                focus_keyword=ai_result.get('focus_keyword'),
                featured_image_url=final_dto.featured_image.url if final_dto.featured_image else None,
                schema_json_ld=json.dumps(final_dto.schema_json_ld, ensure_ascii=False, indent=2),
                status='processed',
                feed_type=feed_key,
                attribution=final_dto.attribution
            )
            db.session.add(new_article)
            db.session.commit()
            logger.info(f"Article '{final_dto.title}' saved to database with status 'processed'.")

            # Step 7: Publish the newly created article to WordPress
            self.wordpress_publisher.publish_article(new_article.id)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save article {source_url} to database. It will be retried later. Error: {e}", exc_info=True)
            return  # Exit if we can't save, to avoid trying to publish an unsaved article


    def cleanup_cycle(self):
        """Database cleanup cycle"""
        # Adicionado para garantir que o ciclo de limpeza tenha acesso ao contexto da aplicação.
        with self.app.app_context():
            try:
                logger.info("Starting cleanup cycle")
                self.rss_monitor.cleanup_old_articles()
                logger.info("Cleanup cycle completed")
            except Exception as e:
                logger.error(f"Error in cleanup cycle: {str(e)}", exc_info=True)

    def execute_now(self):
        """Execute automation cycle immediately"""
        logger.info("Manual execution triggered")
        # Adicionado para garantir que a execução manual tenha acesso ao contexto da aplicação.
        with self.app.app_context():
            self.automation_cycle()

    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }

# Global scheduler instance
scheduler_instance = None

def init_scheduler(app):
    """Initialize global scheduler"""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = ContentAutomationScheduler()
        scheduler_instance.app = app  # Pass the app context to the scheduler instance
        scheduler_instance.start()

        # Log de verificação para confirmar que os jobs foram carregados corretamente
        for job in scheduler_instance.scheduler.get_jobs():
            logger.info(f"[JOB LOADED] id='{job.id}', name='{job.name}', trigger='{job.trigger}', next_run='{job.next_run_time}'")
    return scheduler_instance

def get_scheduler():
    """Get global scheduler instance"""
    return scheduler_instance
