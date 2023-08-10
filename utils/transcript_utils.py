import os
from typing import Optional, List

TRANSCRIPTS_DIRECTORY = os.path.join(os.path.dirname(__file__), "transcript_storage")

def get_transcript_path(conversation_id: str) -> str:
    return os.path.join(TRANSCRIPTS_DIRECTORY, f"{conversation_id}.txt")

def transcript_exists(conversation_id: str) -> bool:
    transcript_path = get_transcript_path(conversation_id)
    return os.path.exists(transcript_path)

def list_transcripts() -> List[str]:
    return [
        os.path.splitext(file)[0]
        for file in os.listdir(TRANSCRIPTS_DIRECTORY)
        if file.endswith(".txt")
    ]

def create_transcript(conversation_id: str, transcript: str) -> None:
    transcript_path = get_transcript_path(conversation_id)
    with open(transcript_path, "a") as f:
        f.write(transcript)


def get_transcript(conversation_id: str) -> Optional[str]:
    transcript_path = get_transcript_path(conversation_id)
    if os.path.exists(transcript_path):
        with open(transcript_path, "r") as f:
            return f.read()
    return None


def delete_transcript(conversation_id: str) -> bool:
    transcript_path = get_transcript_path(conversation_id)
    if os.path.exists(transcript_path):
        os.remove(transcript_path)
        return True
    return False





