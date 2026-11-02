import os
from app import create_app

# Gunicorn expects 'app' or 'application'
env = os.environ.get('FLASK_ENV', 'production')
application = create_app(env)
app = application

if __name__ == '__main__':
    # Local direct execution
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
