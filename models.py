from extensions import db

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    user_passwd = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<User {self.user_name}>'

    
