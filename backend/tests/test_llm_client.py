from app import llm_client
from app.config import Settings
from app.llm_client import build_rag_messages, generate_answer


def test_build_rag_messages_includes_context_and_question():
    messages = build_rag_messages("What is diabetes?", ["Diabetes is high blood sugar."])
    assert messages[0].content == llm_client.SYSTEM_PROMPT
    assert "Diabetes is high blood sugar." in messages[1].content
    assert "What is diabetes?" in messages[1].content


def test_build_rag_messages_handles_empty_context():
    messages = build_rag_messages("What is diabetes?", [])
    assert "no relevant reference material" in messages[1].content


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeChatModel:
    def __init__(self, content):
        self._content = content

    def invoke(self, messages):
        return FakeResponse(self._content)


def test_generate_answer_uses_chat_model_and_returns_content(monkeypatch):
    monkeypatch.setattr(llm_client, "get_chat_model", lambda api_key, model: FakeChatModel("Diabetes info."))

    settings = Settings(groq_api_key="test-key", groq_model="test-model")
    answer = generate_answer(settings, "What is diabetes?", ["context"])

    assert answer == "Diabetes info."
