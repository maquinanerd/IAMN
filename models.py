from datetime import datetime
from extensions import db

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    
    # Core identifier and status
    source_url = db.Column(db.String(1024), nullable=False, unique=True, index=True)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True) # e.g., pending, extracting, processing, published, failed
    
    # Data from source
    original_title = db.Column(db.String(512))
    original_content = db.Column(db.Text)
    feed_type = db.Column(db.String(100), index=True) # e.g., 'screenrant_filmes_tv'
    
    # Data from AI processing
    titulo_final = db.Column(db.String(512))
    conteudo_final = db.Column(db.Text)
    meta_description = db.Column(db.String(1024))
    slug = db.Column(db.String(512), index=True)
    focus_keyword = db.Column(db.String(100))
    categoria = db.Column(db.String(100))
    obra_principal = db.Column(db.String(255))
    tags = db.Column(db.Text)  # Storing as JSON string
    schema_json_ld = db.Column(db.Text)
    attribution = db.Column(db.Text)
    
    # WordPress publishing data
    featured_image_url = db.Column(db.String(1024))
    wordpress_id = db.Column(db.Integer)
    wordpress_url = db.Column(db.String(1024))
    
    # Timestamps and metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime)
    published_at = db.Column(db.DateTime)
    processing_time = db.Column(db.Integer) # in seconds
    ai_used = db.Column(db.String(100))
    error_message = db.Column(db.Text)

    logs = db.relationship('ProcessingLog', backref='article', lazy=True, cascade="all, delete-orphan")
    media = db.relationship('ExtractedMedia', backref='article', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Article {self.id} - {self.original_title[:50] if self.original_title else "N/A"}>'

class ProcessingLog(db.Model):
    __tablename__ = 'processing_logs'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False) # e.g., 'AI_PROCESSING', 'PUBLISHING'
    message = db.Column(db.Text)
    ai_used = db.Column(db.String(100))
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExtractedMedia(db.Model):
    __tablename__ = 'extracted_media'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    media_type = db.Column(db.String(50)) # 'image', 'youtube', 'twitter', etc.
    url = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, downloaded, uploaded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)