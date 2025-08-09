import logging
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from urllib.parse import urlparse
from services.rss_monitor import RSSMonitor
from services.ai_processor import AIProcessor
from services.wordpress_publisher import WordPressPublisher
from services.content_extractor import ContentExtractor
from services.schema_generator import SchemaGenerator
from dto import PublishedArticleDTO, FeaturedImageDTO
from config import SCHEDULE_CONFIG, PIPELINE_CONFIG, UNIVERSAL_PROMPT, WORDPRESS_CONFIG

logger = logging.getLogger(__name__)

# Reduz o ruído de logs do APScheduler durante o desenvolvimento
logging.getLogger('apscheduler').setLevel(logging.WARNING)

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
        An optional limit can be provided to override the default number of articles per run.
        """
        with self.app.app_context():
            try:
                logger.info("=== Starting automation cycle ===")
                effective_limit = limit if limit is not None else SCHEDULE_CONFIG['max_articles_per_run']
                logger.info(f"Step 1: Fetching up to {effective_limit} new article URLs from RSS feeds...")
                articles_to_process = self.rss_monitor.fetch_new_articles(limit=effective_limit)
                logger.info(f"Found {len(articles_to_process)} new articles to process.")

                for article_data in articles_to_process:
                    source_url = article_data.link
                    logger.info(f"--- Processing URL: {source_url} ---")

                    # Step 2: Extract and sanitize content
                    extracted_data = self.content_extractor.extract(source_url)
                    if not extracted_data:
                        logger.error(f"Extraction failed for {source_url}, skipping.")
                        continue

                    # Step 3: Rewrite with AI
                    # The prompt requires a domain for internal links. Let's extract it from the WordPress URL.
                    wp_url = WORDPRESS_CONFIG.get('url', '')
                    parsed_url = urlparse(wp_url)
                    domain = f"{parsed_url.scheme}://{parsed_url.netloc}" if wp_url else ""

                    # Determine the category from the feed type (e.g., 'movies_screenrant' -> 'movies')
                    category = article_data.feed_type.split('_')[0]

                    prompt = UNIVERSAL_PROMPT.format(
                        title=extracted_data['metadata']['title'] or "Sem título",
                        excerpt=extracted_data['metadata']['summary'] or "Sem resumo",
                        domain=domain,
                        content=extracted_data['content_html']
                    )
                    ai_result_json = self.ai_processor.send_prompt(prompt, category=category)

                    if not ai_result_json:
                        logger.error(f"AI processing failed for {source_url} after trying all models. Skipping article.")
                        continue

                    ai_result = json.loads(ai_result_json)

                    # Step 4: Generate Schema.org
                    schema_ld = self.schema_generator.generate_news_article_schema(
                        headline=ai_result['titulo_final'],
                        summary=ai_result['meta_description'],
                        image_url=extracted_data['metadata']['featured_image'],
                        canonical_url=extracted_data['metadata']['canonical_url'],
                        date_published=extracted_data['metadata']['published_time'],
                        author_name=extracted_data['metadata']['author'],
                        publisher_name=PIPELINE_CONFIG['publisher_name'],
                        publisher_logo_url=PIPELINE_CONFIG['publisher_logo_url']
                    )

                    # Step 5: Assemble the final DTO
                    final_dto = PublishedArticleDTO(
                        source_url=source_url,
                        canonical_url=extracted_data['metadata']['canonical_url'],
                        title=ai_result['titulo_final'],
                        summary=ai_result['meta_description'],
                        slug=self.wordpress_publisher.slugify(ai_result['titulo_final']),
                        featured_image=FeaturedImageDTO(url=extracted_data['metadata']['featured_image'], alt=ai_result['titulo_final']),
                        content_html=ai_result['conteudo_final'],
                        tags=ai_result['tags'],
                        category=ai_result['categoria'],
                        schema_json_ld=schema_ld,
                        attribution=PIPELINE_CONFIG['attribution_policy'].format(domain=urlparse(source_url).netloc)
                    )

                    # Step 6: Publish to WordPress
                    # self.wordpress_publisher.publish(final_dto) # This method needs to be adapted
                    logger.info(f"Article '{final_dto.title}' is ready for publishing.")

                logger.info(f"=== Cycle completed. Processed {len(articles_to_process)} articles. ===")

            except Exception as e:
                logger.error(f"Error in automation cycle: {str(e)}", exc_info=True)

    def cleanup_cycle(self):
        """Database cleanup cycle"""
        with self.app.app_context():
            try:
                logger.info("Starting cleanup cycle")
                self.rss_monitor.cleanup_old_articles()
                logger.info("Cleanup cycle completed")
            except Exception as e:
                logger.error(f"Error in cleanup cycle: {str(e)}")

    def execute_now(self):
        """Execute automation cycle immediately"""
        logger.info("Manual execution triggered")
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
