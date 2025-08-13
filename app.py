import os
import logging
from flask import Flask
# Adicionado para carregar o arquivo .env
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
# Reduce noise from the trafilatura library during normal operation
logging.getLogger('trafilatura').setLevel(logging.WARNING)
# Reduce noise from other verbose libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('htmldate').setLevel(logging.WARNING)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Create the app
app = Flask(__name__)

# Set debug mode from environment variable. This is crucial for the scheduler
# to initialize correctly, especially with the reloader in debug mode.
# For development, set FLASK_DEBUG=1 in your .env file.
app.debug = os.environ.get("FLASK_DEBUG", "0") == "1"

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

# Initialize and start the scheduler. The condition below is crucial to avoid
# running the scheduler twice when Flask is in debug mode (which uses a reloader).
#
# 1. `not app.debug`: In a production environment (debug=False), the scheduler starts.
# 2. `os.environ.get('WERKZEUG_RUN_MAIN') == 'true'`: In debug mode, Flask runs two
#    processes. This ensures the scheduler only starts in the 'reloaded' child process,
#    not the parent monitoring process.
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    from services.scheduler import init_scheduler
    init_scheduler(app)

# Adicionado para permitir a execução direta para desenvolvimento
if __name__ == '__main__':
    app.run()
