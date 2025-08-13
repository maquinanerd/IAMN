import logging
import time
import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db
from config import WORDPRESS_CONFIG
from services.scheduler import init_scheduler, get_scheduler

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Carrega as variáveis de ambiente de um arquivo .env no início da aplicação.
# Isso é útil para o desenvolvimento local, para não expor chaves no código.
if not load_dotenv():
    logging.warning("Arquivo .env não encontrado. As configurações devem ser fornecidas como variáveis de ambiente.")
else:
    logging.info("Arquivo .env carregado com sucesso.")

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    # Configuração do banco de dados.
    # Prioriza a variável de ambiente DATABASE_URL (para PostgreSQL em produção)
    # e usa um banco de dados SQLite local como fallback para desenvolvimento.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Inicializa as extensões
    db.init_app(app)

    # Cria as tabelas do banco de dados se não existirem
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    scheduler = None

    try:
        # O contexto da aplicação é necessário para o scheduler acessar o banco de dados
        with app.app_context():
            # Inicializa e inicia o scheduler
            scheduler = init_scheduler(app)
            logging.info("Aplicação iniciada. O scheduler está rodando em background.")
            logging.info("Pressione Ctrl+C para encerrar a aplicação de forma segura.")

        # Mantém o script principal rodando para que o scheduler em background continue
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Sinal de interrupção (Ctrl+C) recebido. Encerrando...")
    finally:
        if scheduler and scheduler.is_running:
            logging.info("Encerrando o scheduler...")
            scheduler.stop()
            logging.info("Scheduler encerrado com sucesso.")