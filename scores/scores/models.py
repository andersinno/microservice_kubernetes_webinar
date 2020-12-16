from sqlalchemy import Column, Integer, String
from .database import Base


class Score(Base):
    __tablename__ = "Score"

    id: int = Column(Integer, primary_key=True, index=True)
    user: str = Column(String(255), index=True)
    score: str = Column(Integer(), default=1)
