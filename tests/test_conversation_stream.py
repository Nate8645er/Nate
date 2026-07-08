"""Tests für das satzweise Streamen im ConversationManager."""

from jarvis.core.conversation import ConversationManager


class FakeStreamingClient:
    """Stellt sich wie ein LLM-Client mit chat_stream an."""

    def __init__(self, pieces: list[str]):
        self.pieces = pieces
        self.received_messages = None

    def chat_stream(self, prompt=None, messages=None):
        self.received_messages = messages
        yield from self.pieces


class FakeBlockingClient:
    """Alter Client ohne chat_stream - nur chat()."""

    def __init__(self, answer: str):
        self.answer = answer

    def chat(self, prompt=None, messages=None):
        return self.answer


def test_ask_stream_liefert_saetze_waehrend_der_antwort():
    client = FakeStreamingClient(
        ["Der Termin ", "steht. Ich habe ", "ihn eingetragen."]
    )
    conversation = ConversationManager(client, system_prompt="Test")

    sentences = list(conversation.ask_stream("Trag den Termin ein"))

    assert sentences == ["Der Termin steht.", "Ich habe ihn eingetragen."]
    # Verlauf enthält am Ende die komplette Antwort in einem Stück
    assert conversation.messages[-1] == {
        "role": "assistant",
        "content": "Der Termin steht. Ich habe ihn eingetragen.",
    }
    assert conversation.messages[-2] == {
        "role": "user",
        "content": "Trag den Termin ein",
    }


def test_ask_stream_faellt_auf_blocking_chat_zurueck():
    client = FakeBlockingClient("Alles klar. Erledigt!")
    conversation = ConversationManager(client, system_prompt="Test")

    sentences = list(conversation.ask_stream("Mach das bitte"))

    assert sentences == ["Alles klar.", "Erledigt!"]
    assert conversation.messages[-1]["content"] == "Alles klar. Erledigt!"


def test_ask_stream_kuerzt_verlauf_wie_ask():
    client = FakeStreamingClient(["Ok."])
    conversation = ConversationManager(
        client, system_prompt="Test", max_history_messages=2
    )
    list(conversation.ask_stream("eins"))
    list(conversation.ask_stream("zwei"))
    list(conversation.ask_stream("drei"))
    # System-Prompt + maximal 2 Verlaufsnachrichten vor der neuen Antwort
    assert conversation.messages[0]["role"] == "system"
    assert len(conversation.messages) <= 4
