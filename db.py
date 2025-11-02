from sqlmodel import SQLModel, Session, create_engine, Field

class User(SQLModel, table=True):
    id: str = Field(primary_key=True, unique=True)
    email: str | None = None
    fcm_token: str = Field(default="")
    active_token: bool = Field(default=False)
    anonymous: bool = Field(default=True)

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session