#!/usr/bin/env python3
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    try:
        users = User.query.all()
        print(f'Found {len(users)} users:')
        for u in users:
            print(f'- {u.username} ({u.email}) - Active: {u.is_active}')
    except Exception as e:
        print(f'Database error: {e}')