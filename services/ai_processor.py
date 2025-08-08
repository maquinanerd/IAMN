import json
import logging
import time
import re
from datetime import datetime
import google.generativeai as genai
from extensions import db
from models import Article, ProcessingLog
from config import AI_CONFIG, UNIVERSAL_PROMPT

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
                    # Use the modern GenerativeModel API
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",  # Using a current and efficient model
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json"
                        ),
                        client_options={"api_key": api_key}
                    )
                    self.clients[ai_type].append(model)
                    logger.info(f"Initialized {ai_type} AI model #{i+1}")
                except Exception as e:
                    logger.error(f"Failed to initialize {ai_type} AI model #{i+1}: {str(e)}")
            if not self.clients[ai_type]:
                logger.warning(f"No valid API keys found or initialized for AI type: {ai_type}")

    def process_pending_articles(self, max_articles=3):
        """Process pending articles using appropriate AI"""
        pending_articles = Article.query.filter_by(status='pending').limit(max_articles).all()

        processed_count = 0
        for article in pending_articles:
            try:
                start_time = time.time()
                article.status = 'processing'
                db.session.commit()

                # Determine which AI to use based on feed type (e.g., 'movies_screenrant' -> 'movies')
                ai_type = article.feed_type.split('_')[0]

                result = self._process_with_ai(article, ai_type)

                if result:
                    # Update article with AI results
                    article.titulo_final = re.sub(r'</?strong>', '', result.get('titulo_final', ''))
                    article.conteudo_final = self._correct_paragraphs(result.get('conteudo_final'))
                    article.meta_description = result.get('meta_description')
                    article.focus_keyword = result.get('focus_keyword')
                    article.categoria = result.get('categoria')
                    article.obra_principal = result.get('obra_principal')
                    article.tags = json.dumps(result.get('tags', []))
                    article.status = 'processed'
                    article.processed_at = datetime.utcnow()
                    article.processing_time = int(time.time() - start_time)

                    self._log_processing(article.id, 'AI_PROCESSING', 'Successfully processed article', 
                                       article.ai_used, True)

                    processed_count += 1
                    logger.info(f"Successfully processed article: {article.original_title}")
                else:
                    article.status = 'failed'
                    article.error_message = 'AI processing failed'
                    self._log_processing(article.id, 'AI_PROCESSING', 'AI processing failed', 
                                       article.ai_used, False)

                db.session.commit()

            except Exception as e:
                logger.error(f"Error processing article {article.id}: {str(e)}")
                article.status = 'failed'
                article.error_message = str(e)
                db.session.commit()

        return processed_count

    def _process_with_ai(self, article, ai_type):
        """Process article with specified AI type, iterating through available clients on failure."""
        if ai_type not in self.clients or not self.clients[ai_type]:
            logger.error(f"No AI clients configured for type: {ai_type}")
            return None

        for i, model in enumerate(self.clients[ai_type]):
            ai_name = f"{ai_type}_model_#{i+1}"
            logger.info(f"Attempting to process article {article.id} with {ai_name}")
            result = self._call_ai(model, article, ai_name)
            if result:
                article.ai_used = ai_name
                return result
            logger.warning(f"AI call failed with {ai_name}. Trying next model if available.")

        logger.error(f"All AI clients for type {ai_type} failed to process article {article.id}")
        return None

    def _call_ai(self, model, article, ai_name):
        """Make actual AI call with error handling"""
        try:
            prompt = UNIVERSAL_PROMPT.format(
                titulo=article.original_title,
                conteudo=article.original_content
            )
            
            # Use the new API to generate content
            response = model.generate_content(prompt)

            if response.text:
                try:
                    result = json.loads(response.text)
                    required_fields = ['titulo_final', 'conteudo_final', 'meta_description', 
                                     'focus_keyword', 'categoria', 'obra_principal', 'tags']

                    if all(field in result for field in required_fields):
                        return result
                    else:
                        logger.error(f"Missing required fields in AI response from {ai_name}")
                        return None

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from {ai_name}: {str(e)}")
                    return None
            else:
                logger.error(f"Empty response from {ai_name}")
                return None

        except Exception as e:
            logger.error(f"AI call failed for {ai_name}: {str(e)}")
            return None

    def _correct_paragraphs(self, content):
        """Ensure content has proper paragraph structure and format"""
        if not content:
            return content

        # Replace ** with <strong> tags
        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)

        # Split into sentences and regroup into paragraphs
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 5:
            return content  # Keep as is if too short

        # Group sentences into paragraphs (3 sentences per paragraph)
        paragraphs = []
        for i in range(0, len(sentences), 3):
            paragraph_sentences = sentences[i:i+3]
            if paragraph_sentences:
                paragraph = '. '.join(paragraph_sentences)
                if not paragraph.endswith('.'):
                    paragraph += '.'
                paragraphs.append(paragraph)

        return '\n\n'.join(paragraphs)

    def _log_processing(self, article_id, action, message, ai_used, success):
        """Log processing actions"""
        try:
            log = ProcessingLog(
                article_id=article_id,
                action=action,
                message=message,
                ai_used=ai_used,
                success=success
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging processing action: {str(e)}")

    def get_ai_status(self):
        """Get status of all AIs"""
        status = {}
        for ai_type in AI_CONFIG.keys():
            status[ai_type] = {
                'available_keys': len(self.clients.get(ai_type, [])),
                'last_used': self._get_last_used_time(ai_type)
            }
        return status

    def _get_last_used_time(self, ai_type):
        """Get last time an AI was used"""
        last_log = ProcessingLog.query.filter(
            ProcessingLog.ai_used.like(f"{ai_type}%")
        ).order_by(ProcessingLog.created_at.desc()).first()

        return last_log.created_at.isoformat() if last_log else None
