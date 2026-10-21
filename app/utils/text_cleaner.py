import re


def _strip_code_fences(text: str) -> str:
    lines = text.split("\n")
    cleaned: list[str] = []
    in_fence = False
    for line in lines:
        if re.match(r"^```", line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            cleaned.append(line)
    return "\n".join(cleaned)


def _clean_latex(text: str) -> str:
    text = re.sub(r"\$\\rightarrow\$", "->", text)
    text = re.sub(r"\\rightarrow", "->", text)
    text = re.sub(r"\\(?:textbf|textit|texttt|emph)\{([^{}]*)\}", r"\1", text)
    text = text.replace("$", "")
    text = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", text)
    return text


def _clean_emphasis(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)

    lines = []
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("* ") or stripped.startswith("*\t"):
            line = stripped[1:].lstrip()
            line = "- " + line if not line.startswith("-") else line
        lines.append(line)
    text = "\n".join(lines)

    text = re.sub(r"(?<!\*)\*(?!\*|\s)([^*\n]+?)(?<!\s)\*(?!\*)", r"\1", text)
    return text


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_chat_output(text: str) -> str:
    if not text:
        return text
    text = _strip_code_fences(text)
    text = _clean_latex(text)
    text = _clean_emphasis(text)
    text = _normalize_whitespace(text)
    return text.strip()


def truncate_at_sentence(text: str, max_chars: int, ellipsis: str = "...") -> str:
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    cut = max(head.rfind(". "), head.rfind("\n"), head.rfind(": "), head.rfind(" "))
    if cut > max_chars // 2:
        head = head[: cut + 1]
    head = head.strip()
    return f"{head} {ellipsis}".strip()