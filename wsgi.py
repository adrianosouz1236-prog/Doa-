# wsgi.py - Ponto de entrada para o Render
import sys
import os

# Adiciona o diretório back-end ao path
backend_dir = os.path.join(os.path.dirname(__file__), 'back-end')
sys.path.insert(0, backend_dir)

# Agora podemos importar o app
from app import app as application

# Para compatibilidade com gunicorn
app = application

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
