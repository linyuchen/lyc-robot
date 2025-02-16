from src.db import init_db
from src.db.models.ai_chat import ChatModel

db_session = init_db()


def read_chat_model(context_id: str):
    model: ChatModel = db_session.query(ChatModel).filter(ChatModel.context_id == context_id).first()
    if model:
        return model.model


def save_chat_model(context_id: str, model_name: str):
    model: ChatModel = db_session.query(ChatModel).filter(ChatModel.context_id == context_id).first()
    if model:
        model.model = model_name
    else:
        model = ChatModel(context_id=context_id, model=model_name)
        db_session.add(model)
    db_session.commit()
