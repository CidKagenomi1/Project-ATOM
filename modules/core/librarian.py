"""
A.T.O.M. Librarian — 3-Layer Conversation Memory Engine
Layer 1: Working Memory (recent multi-turn messages sent as native Human/AI turns)
Layer 2: Session Memory (rolling structured summary of all older messages in this session)
Layer 3: Cross-Session Memory (condensed profile/topics across all other user sessions)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


WORKING_WINDOW_MESSAGES = 12   # 6 full user-assistant exchanges sent verbatim
SOFT_WARN_MESSAGES = 24        # Suggest starting a new chat (non-blocking)
HIGH_WARN_MESSAGES = 40        # Stronger suggestion (still non-blocking)
SOFT_WARN_TOKENS = 6000
MAX_SUMMARY_CHARS = 2400
MAX_CROSS_SESSION_CHARS = 1500


def _clean_snippet(text: str, max_len: int = 180) -> str:
    """Normalize whitespace and trim a message into a concise snippet."""
    if not text:
        return ""
    s = re.sub(r"```[\s\S]*?```", "[blok kode]", str(text))
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        return s[: max_len - 1].rstrip() + "…"
    return s


def _extract_key_topic(messages: List[Dict[str, Any]]) -> str:
    """Extract the overarching topic from the earliest substantive user messages."""
    user_snippets: List[str] = []
    for m in messages:
        if m.get("role") == "user":
            txt = _clean_snippet(m.get("content", ""), max_len=120)
            if len(txt) >= 4:
                user_snippets.append(txt)
            if len(user_snippets) >= 3:
                break
    return " | ".join(user_snippets)


class Librarian:
    """The Librarian: 3-Layer conversation context & memory manager."""

    def __init__(self, working_window: int = WORKING_WINDOW_MESSAGES):
        self.working_window = working_window
        self.raw_history: List[str] = []           # Backward-compatible flat lines
        self.all_messages: List[Dict[str, str]] = []
        self.working_messages: List[Dict[str, str]] = []
        self.summary: str = ""                     # Layer 2: Session summary
        self.session_topic: str = ""               # Primary topic of current session
        self.cross_session_summary: str = ""       # Layer 3: Cross-session summary
        self.cross_session_count: int = 0

    def load_session_history(
        self,
        history: Optional[List[Dict[str, Any]]] = None,
        cross_session_memory: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Hydrate all 3 memory layers from the full session history and
        condensed summaries of other sessions.
        """
        self.clear()

        normalized: List[Dict[str, str]] = []
        for msg in (history or []):
            if not isinstance(msg, dict):
                continue
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = str(msg.get("content", "") or "").strip()
            if not content:
                continue
            normalized.append({"role": role, "content": content})

        self.all_messages = normalized
        self.session_topic = _extract_key_topic(normalized)

        # Layer 1: Working memory (recent messages as native turns)
        if len(normalized) > self.working_window:
            older = normalized[:-self.working_window]
            self.working_messages = normalized[-self.working_window:]
            self.summary = self._build_session_summary(older)
        else:
            self.working_messages = list(normalized)
            self.summary = ""

        # Maintain backward-compatible raw_history
        for m in self.working_messages:
            prefix = "User" if m["role"] == "user" else "ATOM"
            self.raw_history.append(f"{prefix}: {m['content']}")

        # Layer 3: Cross-session memory
        self.cross_session_summary, self.cross_session_count = self._build_cross_session_summary(
            cross_session_memory or []
        )

    def _build_session_summary(self, older_messages: List[Dict[str, str]]) -> str:
        """
        Build a structured rolling summary covering ALL older messages in this session
        so early topics (e.g., initial subject/entities) are never forgotten.
        """
        if not older_messages:
            return ""

        lines: List[str] = []
        if self.session_topic:
            lines.append(f"- Topik Awal Sesi: {self.session_topic}")

        # Pair older turns chronologically so the full arc of discussion is preserved
        turn_lines: List[str] = []
        i = 0
        turn_num = 1
        while i < len(older_messages):
            msg = older_messages[i]
            if msg["role"] == "user":
                u_snip = _clean_snippet(msg["content"], max_len=140)
                a_snip = ""
                if i + 1 < len(older_messages) and older_messages[i + 1]["role"] == "assistant":
                    a_snip = _clean_snippet(older_messages[i + 1]["content"], max_len=160)
                    i += 2
                else:
                    i += 1
                if a_snip:
                    turn_lines.append(f"  {turn_num}. User: {u_snip} -> ATOM: {a_snip}")
                else:
                    turn_lines.append(f"  {turn_num}. User: {u_snip}")
                turn_num += 1
            else:
                a_snip = _clean_snippet(msg["content"], max_len=140)
                turn_lines.append(f"  {turn_num}. ATOM: {a_snip}")
                turn_num += 1
                i += 1

        # If summary exceeds budget, keep the earliest 3 turns (origin topic) + most recent older turns
        header_text = "\n".join(lines)
        body_text = "\n".join(turn_lines)
        combined = f"{header_text}\n- Ringkasan Alur Sebelumnya ({len(older_messages)} pesan):\n{body_text}".strip()

        if len(combined) > MAX_SUMMARY_CHARS and len(turn_lines) > 6:
            head = turn_lines[:3]
            tail: List[str] = []
            budget = MAX_SUMMARY_CHARS - len(header_text) - sum(len(x) + 1 for x in head) - 120
            for ln in reversed(turn_lines[3:]):
                if budget - (len(ln) + 1) < 0:
                    break
                tail.append(ln)
                budget -= len(ln) + 1
            tail.reverse()
            omitted = len(turn_lines) - len(head) - len(tail)
            mid = [f"  ... ({omitted} pertukaran tengah diringkas ke topik utama di atas) ..."] if omitted > 0 else []
            combined = (
                f"{header_text}\n"
                f"- Ringkasan Alur Sebelumnya ({len(older_messages)} pesan):\n"
                + "\n".join(head + mid + tail)
            ).strip()

        return combined[:MAX_SUMMARY_CHARS]

    def _build_cross_session_summary(self, cross_sessions: List[Dict[str, Any]]) -> tuple[str, int]:
        """Build a concise Layer 3 memory block from other sessions of the same user."""
        if not cross_sessions:
            return "", 0

        entries: List[str] = []
        total_len = 0
        for sess in cross_sessions[:8]:
            if not isinstance(sess, dict):
                continue
            title = _clean_snippet(sess.get("title", ""), max_len=60)
            summary = _clean_snippet(sess.get("summary", ""), max_len=180)
            topics = sess.get("topics") or []
            topic_str = ""
            if isinstance(topics, list) and topics:
                cleaned_topics = [_clean_snippet(str(t), max_len=70) for t in topics[:3] if t]
                if cleaned_topics:
                    topic_str = "; ".join(cleaned_topics)

            if not title and not summary and not topic_str:
                continue

            parts = [f"- [{title or 'Sesi Sebelumnya'}]"]
            if summary:
                parts.append(summary)
            elif topic_str:
                parts.append(topic_str)

            line = " ".join(parts)
            if total_len + len(line) + 1 > MAX_CROSS_SESSION_CHARS:
                break
            entries.append(line)
            total_len += len(line) + 1

        return "\n".join(entries), len(entries)

    def add_interaction(self, user: str, ai: str) -> None:
        """Append a live interaction (used by CLI / standalone mode)."""
        u_str = str(user or "").strip()
        a_str = str(ai or "").strip()
        if u_str:
            self.all_messages.append({"role": "user", "content": u_str})
        if a_str:
            self.all_messages.append({"role": "assistant", "content": a_str})

        if not self.session_topic:
            self.session_topic = _extract_key_topic(self.all_messages)

        if len(self.all_messages) > self.working_window:
            older = self.all_messages[:-self.working_window]
            self.working_messages = self.all_messages[-self.working_window:]
            self.summary = self._build_session_summary(older)
        else:
            self.working_messages = list(self.all_messages)

        self.raw_history = [
            f"{'User' if m['role'] == 'user' else 'ATOM'}: {m['content']}"
            for m in self.working_messages
        ]

    def get_working_messages(self) -> List[Dict[str, str]]:
        """Return Layer 1 recent messages for native multi-turn LLM calls."""
        return list(self.working_messages)

    def get_memory_prompt_block(self) -> str:
        """Return formatted Layer 2 (Session Summary) + Layer 3 (Cross-Session) memory block."""
        sections: List[str] = []

        if self.session_topic and not self.summary:
            sections.append(
                "LAYER 2 — KONTEKS TOPIK SESI AKTIF:\n"
                f"- Topik Utama Sesi Ini: {self.session_topic}"
            )
        elif self.summary:
            sections.append(
                "LAYER 2 — RINGKASAN MEMORI SESI AKTIF (Pesan Awal yang Sudah Dirangkum):\n"
                f"{self.summary}"
            )

        if self.cross_session_summary:
            sections.append(
                "LAYER 3 — MEMORI LINTAS SESI PENGGUNA (Referensi Latar Belakang & Minat Pengguna):\n"
                f"{self.cross_session_summary}\n"
                "(Gunakan memori lintas sesi ini secara natural bila relevan agar pengguna merasa dipahami, "
                "namun tetap prioritaskan topik sesi aktif saat ini.)"
            )

        return "\n\n".join(sections)

    def get_active_topic_hint(self) -> str:
        """Compact topic hint for contextualizing web search queries & typo resolution."""
        parts: List[str] = []
        if self.session_topic:
            parts.append(self.session_topic)
        # Also include the last 2 user messages for recent sub-topic shift
        recent_users = [m["content"] for m in self.working_messages if m["role"] == "user"][-2:]
        for ru in recent_users:
            snip = _clean_snippet(ru, max_len=90)
            if snip and snip not in (self.session_topic or ""):
                parts.append(snip)
        return " | ".join(parts)[:260]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Compute memory health & soft recommendation to start a new chat."""
        total_messages = len(self.all_messages)
        total_chars = sum(len(m.get("content", "")) for m in self.all_messages)
        estimated_tokens = max(0, total_chars // 4)
        summarized_count = max(0, total_messages - len(self.working_messages))

        level = "ok"
        suggest_new_chat = False
        message = ""

        if total_messages >= HIGH_WARN_MESSAGES or estimated_tokens >= SOFT_WARN_TOKENS * 2:
            level = "high"
            suggest_new_chat = True
            message = (
                f"Sesi ini sudah sangat panjang ({total_messages} pesan). "
                "Ringkasan memori tetap aktif, tetapi disarankan memulai obrolan baru agar akurasi & pemahaman tetap maksimal. "
                "Anda tetap bisa melanjutkan di sini jika diinginkan."
            )
        elif total_messages >= SOFT_WARN_MESSAGES or estimated_tokens >= SOFT_WARN_TOKENS:
            level = "warning"
            suggest_new_chat = True
            message = (
                f"Percakapan ini sudah cukup panjang ({total_messages} pesan). "
                "Untuk memori yang lebih tajam, Anda bisa memulai obrolan baru — atau tetap lanjut di sesi ini tanpa masalah."
            )

        return {
            "total_messages": total_messages,
            "estimated_tokens": estimated_tokens,
            "level": level,
            "suggest_new_chat": suggest_new_chat,
            "message": message,
            "layers": {
                "working_messages": len(self.working_messages),
                "session_summarized": summarized_count,
                "cross_sessions": self.cross_session_count,
            },
        }

    def get_context(self) -> str:
        """Backward-compatible flat context string."""
        blocks = []
        mem_block = self.get_memory_prompt_block()
        if mem_block:
            blocks.append(mem_block)
        if self.raw_history:
            blocks.append("\n".join(self.raw_history))
        return "\n\n".join(blocks)

    def clear(self) -> None:
        self.raw_history = []
        self.all_messages = []
        self.working_messages = []
        self.summary = ""
        self.session_topic = ""
        self.cross_session_summary = ""
        self.cross_session_count = 0
