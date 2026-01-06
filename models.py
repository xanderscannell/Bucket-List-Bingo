from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bingo_data = db.relationship('BingoData', backref='user', lazy=True, cascade='all, delete-orphan', uselist=False)
    progress = db.relationship('Progress', backref='user', lazy=True, cascade='all, delete-orphan', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'createdAt': self.created_at.isoformat()
        }

class BingoData(db.Model):
    __tablename__ = 'bingo_data'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False, unique=True)
    items = db.Column(db.Text, nullable=False)  # JSON array of 24 strings
    year = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)  # Denormalized for convenience

    def to_dict(self):
        return {
            'userName': self.user_name,
            'items': json.loads(self.items),
            'year': self.year
        }

    @staticmethod
    def from_dict(user_id, data):
        return BingoData(
            user_id=user_id,
            items=json.dumps(data['items']),
            year=data['year'],
            user_name=data['userName']
        )

class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False, unique=True)
    marked_cells = db.Column(db.Text, nullable=True)  # JSON array of indices
    cell_details = db.Column(db.Text, nullable=True)  # JSON object with details per cell index
    randomized = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'markedCells': json.loads(self.marked_cells) if self.marked_cells else [],
            'cellDetails': json.loads(self.cell_details) if self.cell_details else {},
            'randomized': self.randomized,
            'updatedAt': self.updated_at.isoformat()
        }

    @staticmethod
    def from_dict(user_id, data):
        return Progress(
            user_id=user_id,
            marked_cells=json.dumps(data.get('markedCells', [])),
            cell_details=json.dumps(data.get('cellDetails', {})),
            randomized=data.get('randomized', False)
        )
