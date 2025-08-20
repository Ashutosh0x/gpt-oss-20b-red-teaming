from typing import List, Dict


def to_harmony(conversation: List[Dict[str, str]], reasoning_level: str = "low") -> str:
    """Convert role/content messages to Harmony response string.

    conversation: list of {"role": one of [system, developer, user, assistant], "content": str}
    """
    header = (
        "<|start|>system<|message|>You are ChatGPT, a large language model trained by OpenAI.\n"
        "reasoning: " + reasoning_level + "\n\n"
        "# Valid channels: analysis, commentary, final. Channel must be included for every message.\n"
        "Calls to these tools must go to the commentary channel: 'functions'.<|end|>"
    )
    parts: List[str] = [header]
    role_tags = {
        "system": "system",
        "developer": "developer",
        "user": "user",
        "assistant": "assistant",
    }
    for msg in conversation:
        role = role_tags.get(msg["role"], "user")
        parts.append(f"<|start|>{role}<|message|>{msg['content']}<|end|>")
    return "".join(parts)


