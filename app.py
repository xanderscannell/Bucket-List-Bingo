from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models import db, User, BingoData, Progress
from config import Config
import json
from datetime import datetime, timezone

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
CORS(app)

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Serve the frontend
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# API Routes

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user with bingo data"""
    data = request.json

    # Generate user ID
    user_id = 'user_' + str(int(datetime.now(timezone.utc).timestamp() * 1000))

    # Create user
    user = User(
        id=user_id,
        name=data['userName']
    )

    # Create bingo data
    bingo_data = BingoData.from_dict(user_id, data)

    # Create empty progress
    progress = Progress(user_id=user_id)

    db.session.add(user)
    db.session.add(bingo_data)
    db.session.add(progress)
    db.session.commit()

    return jsonify({
        'user': user.to_dict(),
        'bingoData': bingo_data.to_dict(),
        'progress': progress.to_dict()
    }), 201

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and all associated data"""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@app.route('/api/users/<user_id>/data', methods=['GET'])
def get_user_bingo_data(user_id):
    """Get user's bingo data"""
    bingo_data = BingoData.query.filter_by(user_id=user_id).first_or_404()
    return jsonify(bingo_data.to_dict())

@app.route('/api/users/<user_id>/data', methods=['PUT'])
def update_user_bingo_data(user_id):
    """Update user's bingo data"""
    data = request.json
    bingo_data = BingoData.query.filter_by(user_id=user_id).first_or_404()

    bingo_data.items = json.dumps(data['items'])
    bingo_data.year = data['year']
    bingo_data.user_name = data['userName']

    db.session.commit()
    return jsonify(bingo_data.to_dict())

@app.route('/api/users/<user_id>/progress', methods=['GET'])
def get_user_progress(user_id):
    """Get user's progress"""
    progress = Progress.query.filter_by(user_id=user_id).first_or_404()
    return jsonify(progress.to_dict())

@app.route('/api/users/<user_id>/progress', methods=['PUT'])
def update_user_progress(user_id):
    """Update user's progress"""
    data = request.json
    progress = Progress.query.filter_by(user_id=user_id).first()

    if not progress:
        progress = Progress(user_id=user_id)
        db.session.add(progress)

    if 'markedCells' in data:
        progress.marked_cells = json.dumps(data['markedCells'])
    if 'randomized' in data:
        progress.randomized = data['randomized']

    db.session.commit()
    return jsonify(progress.to_dict())

@app.route('/api/users/<user_id>/randomize', methods=['POST'])
def mark_randomized(user_id):
    """Mark user's card as randomized"""
    progress = Progress.query.filter_by(user_id=user_id).first()

    if not progress:
        progress = Progress(user_id=user_id)
        db.session.add(progress)

    progress.randomized = True
    db.session.commit()

    return jsonify(progress.to_dict())

@app.route('/api/users/<user_id>/reset-progress', methods=['POST'])
def reset_user_progress(user_id):
    """Reset user's progress"""
    progress = Progress.query.filter_by(user_id=user_id).first()

    if progress:
        progress.marked_cells = json.dumps([])
        db.session.commit()

    return jsonify(progress.to_dict() if progress else {'markedCells': [], 'randomized': False})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
