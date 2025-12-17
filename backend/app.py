from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Configure CORS - allow all origins in production for Render deployment
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# Basic security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Allow CORS for all origins in production
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# Health check endpoints
@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "ai-loan-chatbot-backend"})

# Import and register blueprints
from routes.document_routes import document_bp
from routes.chat_routes import chat_bp
from routes.history_routes import history_bp

# Register blueprints
app.register_blueprint(document_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(history_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)