# Instruções para Execução em Produção

Este documento descreve como executar a aplicação em um ambiente de produção usando servidores WSGI recomendados. O modo de depuração do Flask não é seguro nem performático para uso em produção.

## Pré-requisitos

Certifique-se de que todas as dependências do `requirements.txt` estão instaladas no seu ambiente de produção.

```bash
pip install -r requirements.txt
```

## Opção 1: Usando Waitress (Recomendado para Windows)

1. Instale o Waitress: `pip install waitress`
2. Execute a aplicação: `waitress-serve --host=0.0.0.0 --port=5000 app:app`

## Opção 2: Usando Gunicorn (Recomendado para Linux/macOS)

1. Instale o Gunicorn: `pip install gunicorn`
2. Execute a aplicação (exemplo com 2 workers e 4 threads por worker): `gunicorn --workers 2 --threads 4 --bind 0.0.0.0:5000 app:app`