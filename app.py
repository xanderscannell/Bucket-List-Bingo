from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models import db, User, BingoData, Progress
from config import Config
import json
import os
import base64
import sqlite3
import sys
from datetime import datetime, timezone

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
CORS(app)

# Initialize database
db.init_app(app)

def validate_database_schema():
    """
    Validate that the database schema is up to date.
    Prevents app from starting with an outdated schema.
    """
    db_path = os.path.join('instance', 'bingo.db')

    # If database doesn't exist yet, it will be created with correct schema
    if not os.path.exists(db_path):
        print("No existing database found - will create with current schema")
        return True

    # Check if progress table has cell_details column
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(progress)")
    columns = [row[1] for row in cursor.fetchall()]

    conn.close()

    if 'cell_details' not in columns:
        print("\n" + "="*70)
        print("ERROR: Database schema is outdated!")
        print("="*70)
        print("\nThe 'progress' table is missing the 'cell_details' column.")
        print("\nTo fix this, run one of the following migration scripts:")
        print("  1. python migrate_add_cell_details.py")
        print("  2. python migrate_legacy_database.py")
        print("\nThe application will not start until the database is migrated.")
        print("="*70 + "\n")
        return False

    return True

# Validate schema before creating tables
with app.app_context():
    if not validate_database_schema():
        print("Application startup aborted due to schema validation failure.")
        sys.exit(1)

    # Create tables (only creates missing tables, doesn't alter existing ones)
    db.create_all()
    print("Database schema validated successfully")

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
    if 'cellDetails' in data:
        progress.cell_details = json.dumps(data['cellDetails'])
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

@app.route('/api/users/<user_id>/cell/<int:cell_index>/details', methods=['PUT'])
def update_cell_details(user_id, cell_index):
    """Update details for a specific cell"""
    data = request.json
    progress = Progress.query.filter_by(user_id=user_id).first()

    if not progress:
        progress = Progress(user_id=user_id)
        db.session.add(progress)

    # Get existing cell details
    cell_details = json.loads(progress.cell_details) if progress.cell_details else {}

    # Update details for this cell
    cell_details[str(cell_index)] = {
        'photos': data.get('photos', []),  # Array of base64 encoded images
        'date': data.get('date'),
        'notes': data.get('notes', '')
    }

    progress.cell_details = json.dumps(cell_details)
    db.session.commit()

    return jsonify(progress.to_dict())

@app.route('/api/users/<user_id>/cell/<int:cell_index>/details', methods=['GET'])
def get_cell_details(user_id, cell_index):
    """Get details for a specific cell"""
    progress = Progress.query.filter_by(user_id=user_id).first()

    if not progress or not progress.cell_details:
        return jsonify(None)

    cell_details = json.loads(progress.cell_details)
    return jsonify(cell_details.get(str(cell_index)))

@app.route('/api/users/<user_id>/cell/<int:cell_index>/details', methods=['DELETE'])
def delete_cell_details(user_id, cell_index):
    """Delete details for a specific cell"""
    progress = Progress.query.filter_by(user_id=user_id).first()

    if progress and progress.cell_details:
        cell_details = json.loads(progress.cell_details)
        if str(cell_index) in cell_details:
            del cell_details[str(cell_index)]
            progress.cell_details = json.dumps(cell_details)
            db.session.commit()

    return jsonify({'success': True})

@app.route('/api/activity/feed', methods=['GET'])
def get_activity_feed():
    """Get chronological feed of all completions across all users"""
    activities = []

    # Query all users with their progress and bingo data
    users = User.query.all()

    for user in users:
        progress = Progress.query.filter_by(user_id=user.id).first()
        bingo_data = BingoData.query.filter_by(user_id=user.id).first()

        if not progress or not progress.cell_details or not bingo_data:
            continue

        cell_details = json.loads(progress.cell_details)
        items = json.loads(bingo_data.items)

        # Extract each completion
        for cell_index_str, details in cell_details.items():
            cell_index = int(cell_index_str)

            # Skip if no date (shouldn't happen with new flow)
            if not details.get('date'):
                continue

            # Get the item text
            # Note: cell_index is an item index (0-23), not a grid position
            # The free space (grid position 12) is never stored in cell_details
            item_text = items[cell_index]

            # Skip free space
            if cell_index == 12:
                continue

            # Get first photo as thumbnail if available
            photos = details.get('photos', [])
            photo_thumbnail = photos[0] if photos else None

            activity = {
                'userId': user.id,
                'userName': user.name,
                'itemText': item_text,
                'cellIndex': cell_index,
                'date': details['date'],
                'photoThumbnail': photo_thumbnail,
                'hasPhotos': len(photos) > 0,
                'notes': details.get('notes', '')
            }

            activities.append(activity)

    # Sort by date (most recent first), with user ID as tiebreaker
    activities.sort(key=lambda x: (x['date'], x['userId']), reverse=True)

    return jsonify(activities)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
