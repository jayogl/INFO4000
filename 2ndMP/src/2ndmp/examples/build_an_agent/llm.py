"""llm.py -- plumbing we do NOT teach. One function that talks to Ollama, plus two tiny helpers.

   MODEL=qwen3:8b uv run python s5_agent_loop.py      # pick another model
"""
import os
import re
import sys

import ollama

MODEL = os.environ.get("MODEL", "qwen3:4b")
DEFAULT_QUESTION = ("A 300 mm steel cantilever beam, 20 mm wide and 10 mm tall, carries a 100 N load at its free end. "
                    "How much does it deflect, and is it safe?")


def question() -> str:
    """The question to ask: first command-line argument, or the default."""
    return sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION


def strip_thinking(text: str) -> str:
    """Qwen3 sometimes leaks its reasoning into the answer. Remove it."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    return text.split("</think>")[-1].replace("<think>", "").strip()


def chat(messages, tools=None):
    kw = dict(model=MODEL, messages=messages, options={"temperature": 0})
    if tools:
        kw["tools"] = tools
    try:
        return ollama.chat(**kw, think=False)                 # switch off 'thinking' for speed
    except (TypeError, ollama.ResponseError) as e:
        if isinstance(e, ollama.ResponseError) and "think" not in str(e).lower():
            raise                                              # a real error
        return ollama.chat(**kw)                               # this model has no thinking mode
