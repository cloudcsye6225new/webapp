from sqlalchemy import Column, VARCHAR, DateTime, Integer, Sequence
from datetime import datetime
from database import Base

# Define a sequence for the id column
user_id_seq = Sequence('user_id_seq')

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, user_id_seq, primary_key=True, server_default=user_id_seq.next_value(), index=True)
    first_name = Column(VARCHAR, index=True)
    last_name = Column(VARCHAR, index=True)
    email = Column(VARCHAR, index=True)
    password = Column(VARCHAR, index=True)
    account_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    account_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
