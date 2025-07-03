from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from trading_app.db import get_db

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        db_conn = get_db()
        user_data = db_conn.execute(
            'SELECT id, username, password FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password'])
        return None

    @staticmethod
    def get_by_username(username):
        db_conn = get_db()
        user_data = db_conn.execute(
            'SELECT id, username, password FROM users WHERE username = ?', (username,)
        ).fetchone()
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password'])
        return None
