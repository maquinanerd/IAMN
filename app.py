import os
import logging
from flask import Flask
# Adicionado para carregar o arquivo .env
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Create the app
app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_SECRET", "content-automation-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
os.makedirs(app.instance_path, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

# Import and register routes
from routes.dashboard import dashboard_bp
from routes.api import api_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Initialize and start the scheduler, ensuring it doesn't run in the reloader process
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    from services.scheduler import init_scheduler
    init_scheduler()

# Adicionado para permitir a execução direta para desenvolvimento
if __name__ == '__main__':
    app.run(debug=True)
