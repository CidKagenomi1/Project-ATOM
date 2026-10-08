"""
A.T.O.M. - Deep Reasoning & Chain of Thought (CoT) Parser
Extracts cognitive thinking tokens and internal reasoning traces from:
- Tags: <think>, <thought>, <thinking> (e.g., DeepSeek-R1, QwQ, Qwen Reasoning, Ollama)
- API Payload fields: 'reasoning_content', 'reasoning' (DeepSeek API, OpenRouter, Groq)
- LangChain metadata: response_metadata / additional_kwargs

Separates raw internal thinking from the final user response so that:
1. The main response bubble remains pristine and markdown-rendered.
2. The extracted reasoning appears neatly structured inside ATOM's 'View Reasoning' UI accordion.
3. Chat memory (Librarian) is not polluted by redundant internal thought tokens.
"""

import re
from typing import Tuple, List, Dict, Optional, Any

# Regex to match think tags (including multi-line and unclosed trailing tags)
THINK_TAG_REGEX = re.compile(
    r"<(think|thought|thinking)>(.*?)(?:<\/\1>|$)",
    re.DOTALL | re.IGNORECASE
)


def extract_reasoning(
    raw_content: str,
    extra_reasoning: Optional[str] = None
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Parses thinking / reasoning from raw content and optional extra reasoning strings.

    Returns:
        tuple (clean_response, extracted_thinking_steps)
    """
    if not raw_content and not extra_reasoning:
        return "", []

    extracted_thoughts: List[str] = []

    # 1. Process explicit extra_reasoning if provided by provider API
    if extra_reasoning and isinstance(extra_reasoning, str) and extra_reasoning.strip():
        cleaned_extra = extra_reasoning.strip()
        # Strip internal tags if accidentally wrapped
        cleaned_extra = THINK_TAG_REGEX.sub(r"\2", cleaned_extra).strip()
        if cleaned_extra:
            extracted_thoughts.append(cleaned_extra)

    # 2. Extract from tags in raw_content
    clean_content = str(raw_content or "")
    matches = list(THINK_TAG_REGEX.finditer(clean_content))

    if matches:
        for m in matches:
            thought_text = m.group(2).strip()
            if thought_text and thought_text not in extracted_thoughts:
                extracted_thoughts.append(thought_text)

        # Remove thinking blocks from main content
        clean_content = THINK_TAG_REGEX.sub("", clean_content).strip()

    # Fallback if the model exhausted tokens during reasoning and produced no final answer
    if not clean_content and extracted_thoughts:
        clean_content = "*(Model menyelesaikan fase reasoning, namun tidak menghasilkan kesimpulan lanjutan.)*"

    # 3. Format as ATOM thinking steps
    reasoning_steps: List[Dict[str, str]] = []
    for idx, thought in enumerate(extracted_thoughts):
        label = "[DEEP REASONING]" if len(extracted_thoughts) == 1 else f"[REASONING #{idx+1}]"
        reasoning_steps.append({
            "step": label,
            "detail": thought
        })

    return clean_content, reasoning_steps


def extract_from_langchain_response(response_obj: Any) -> Tuple[str, Optional[str]]:
    """
    Helper to extract raw content and potential reasoning_content from a LangChain AIMessage.
    """
    content = ""
    extra_reasoning = None

    if hasattr(response_obj, "content"):
        raw_c = response_obj.content
        if isinstance(raw_c, list):
            content = raw_c[0].get("text", str(raw_c[0])) if raw_c else ""
        else:
            content = str(raw_c)
    else:
        content = str(response_obj)

    # Check additional_kwargs & response_metadata
    if hasattr(response_obj, "additional_kwargs") and isinstance(response_obj.additional_kwargs, dict):
        extra_reasoning = (
            response_obj.additional_kwargs.get("reasoning_content") or
            response_obj.additional_kwargs.get("reasoning")
        )

    if not extra_reasoning and hasattr(response_obj, "response_metadata") and isinstance(response_obj.response_metadata, dict):
        extra_reasoning = (
            response_obj.response_metadata.get("reasoning_content") or
            response_obj.response_metadata.get("reasoning") or
            response_obj.response_metadata.get("thinking_process")
        )

    return content, extra_reasoning
