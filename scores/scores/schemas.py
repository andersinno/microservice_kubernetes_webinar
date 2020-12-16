from pydantic.main import BaseModel


class Score(BaseModel):
    user: str
    score: int

    class Config:
        orm_mode = True
