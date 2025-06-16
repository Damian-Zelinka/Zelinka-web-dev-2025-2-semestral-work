import base64
import datetime
from extensions import db 
from sqlalchemy import LargeBinary, event, update

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(80), unique=False, nullable=True)
    last_name = db.Column(db.String(80), unique=False, nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    status = db.Column(db.String(20), default='user')
    profile_picture_data = db.Column(db.LargeBinary)
    profile_picture_type = db.Column(db.String(20))
    reactions = db.relationship('Reaction', back_populates='user')
    comments = db.relationship('Comment', back_populates='user', cascade='all, delete-orphan')

    def to_json(self):
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "status": self.status,
            "profile_picture": self.get_profile_picture_url()
        }
    
    def get_profile_picture_url(self):
        if self.profile_picture_data and self.profile_picture_type:
            return f"data:{self.profile_picture_type};base64,{base64.b64encode(self.profile_picture_data).decode('utf-8')}"
        return None

    

class Landmark(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(180), unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=False)
    image_data = db.Column(LargeBinary, nullable=False)
    mime_type = db.Column(db.String(20), nullable=False)
    likes = db.Column(db.Integer, unique=False, nullable=False, default=0)
    dislikes = db.Column(db.Integer, unique=False, nullable=False, default=0)
    latitude = db.Column(db.Float, unique=False, nullable=False)
    longitude = db.Column(db.Float, unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('landmarks', lazy=True))
    reactions = db.relationship('Reaction', back_populates='landmark')

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": f"data:{self.mime_type};base64,{base64.b64encode(self.image_data).decode('utf-8')}",
            "likes": self.likes,
            "dislikes": self.dislikes,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "user_id": self.user_id,
            "comments": [{
                "id": comment.id,
                "text": comment.text,
                "likes": comment.likes,
                "dislikes": comment.dislikes,
                "date_of_creation": comment.date_of_creation.isoformat(),
                "user_id": comment.user_id,
                "username": comment.user.username,
                "profile_picture": comment.user.get_profile_picture_url()
            } for comment in self.comments]
        }
    


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    date_of_creation = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    landmark_id = db.Column(db.Integer, db.ForeignKey('landmark.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', back_populates='comments')
    landmark = db.relationship('Landmark', backref=db.backref('comments', lazy=True))

    def to_json(self):
        return {
            "id": self.id,
            "text": self.text,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "date_of_creation": self.date_of_creation.isoformat(),
            "landmark_id": self.landmark_id,
            "user_id": self.user_id,
            "username": self.user.username
        }
    


class Reaction(db.Model):
    __tablename__ = 'reaction'
    
    reaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    landmark_id = db.Column(db.Integer, db.ForeignKey('landmark.id'), nullable=False)
    value = db.Column(db.Enum('like', 'dislike', name='reaction_types'), nullable=False)

    landmark = db.relationship('Landmark', back_populates='reactions')
    user = db.relationship('User', back_populates='reactions')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'landmark_id', name='uq_user_landmark'),
    )

    def to_json(self):
        return {
            "reaction_id": self.reaction_id,
            "user_id": self.user_id,
            "landmark_id": self.landmark_id,
            "value": self.value
        }
    


def increment_landmark_reaction(mapper, connection, target):
    stmt = update(Landmark).where(Landmark.id == target.landmark_id)
    if target.value == 'like':
        stmt = stmt.values(likes=Landmark.likes + 1)
    else:
        stmt = stmt.values(dislikes=Landmark.dislikes + 1)
    connection.execute(stmt)

def decrement_landmark_reaction(mapper, connection, target):
    stmt = update(Landmark).where(Landmark.id == target.landmark_id)
    if target.value == 'like':
        stmt = stmt.values(likes=Landmark.likes - 1)
    else:
        stmt = stmt.values(dislikes=Landmark.dislikes - 1)
    connection.execute(stmt)

def update_landmark_reaction(mapper, connection, target):
    hist = db.inspect(target).attrs.value.history
    if hist.deleted:
        old_value = hist.deleted[0]
        new_value = target.value
        
        stmt = update(Landmark).where(Landmark.id == target.landmark_id)
        if old_value == 'like':
            stmt = stmt.values(likes=Landmark.likes - 1)
        else:
            stmt = stmt.values(dislikes=Landmark.dislikes - 1)
        connection.execute(stmt)
        
        stmt = update(Landmark).where(Landmark.id == target.landmark_id)
        if new_value == 'like':
            stmt = stmt.values(likes=Landmark.likes + 1)
        else:
            stmt = stmt.values(dislikes=Landmark.dislikes + 1)
        connection.execute(stmt)

event.listen(Reaction, 'after_insert', increment_landmark_reaction)
event.listen(Reaction, 'before_delete', decrement_landmark_reaction)
event.listen(Reaction, 'after_update', update_landmark_reaction)

print("[DEBUG] Event listeners registered!")