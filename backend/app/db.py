from sqlmodel import SQLModel, create_engine, Session

# SQLite file in backend/ folder
engine = create_engine("sqlite:///./thesis_graph.db", echo=False)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
