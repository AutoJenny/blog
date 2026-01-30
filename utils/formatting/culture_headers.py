"""
Culture / Heritage Facebook header formatting.

Applies to culture_fact (Monday) and heritage_fact (Thursday) only.
Header strings are exact, hard-coded; no DB access, no side effects.

Shared with preview/publish: normalise_text_whitespace() is the single helper
for line endings, trim, collapse blank lines. See instruction doc: Preview should
match real Facebook post (images, emojis, formatting).
"""

# A1: Header strings (exact, hard-coded)
_HEADERS = {
    "culture_fact": "UNDERSTANDING SCOTLAND",
    "heritage_fact": "SCOTTISH HERITAGE",
}


def normalise_text_whitespace(text: str) -> str:
    """
    General helper: normalise line endings, trim lines, remove leading/trailing
    blank lines, collapse runs of 3+ blank lines to 2, no trailing spaces,
    at most one trailing newline (prefer none). Re-used by culture/heritage
    formatter and any future type formatting. Does not strip or replace emojis.
    """
    if not text:
        return ""
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip().lstrip() for line in s.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    result_lines = []
    i = 0
    while i < len(lines):
        if lines[i] == "":
            run_len = 0
            while i < len(lines) and lines[i] == "":
                run_len += 1
                i += 1
            if run_len >= 3:
                result_lines.append("")
                result_lines.append("")
            else:
                for _ in range(run_len):
                    result_lines.append("")
        else:
            result_lines.append(lines[i])
            i += 1
    out = "\n".join(result_lines) if result_lines else ""
    while out and out[-1] == "\n":
        out = out[:-1]
    return out


def _normalise_input(text: str) -> str:
    """A4: Normalise before applying header (uses shared normalise_text_whitespace)."""
    return normalise_text_whitespace(text)


def _normalise_output(s: str) -> str:
    """A4: After formatting — no trailing spaces, at most one trailing newline (prefer none)."""
    if not s:
        return ""
    # No trailing spaces on any line
    lines = [line.rstrip() for line in s.split("\n")]
    # Remove trailing empty lines, then ensure at most one trailing newline (prefer none)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) if lines else ""


def apply_culture_or_heritage_header(content_type: str, generated_content: str) -> str:
    """
    Apply authoritative header to culture_fact or heritage_fact content only.

    A1: culture_fact → UNDERSTANDING SCOTLAND, heritage_fact → SCOTTISH HERITAGE.
    A2: Header UPPERCASE (already in map).
    A3: Final text = HEADER + "\\n\\n" + title_line + "\\n" + body (one blank line after header, one newline between title and body).
    A4: Normalise input (\\r\\n → \\n, trim lines, remove leading/trailing empty lines, collapse 3+ newlines to 2); normalise output (no trailing spaces, at most one trailing newline).
    A5: No emojis, hashtags, CTAs, URLs, rewriting — this function only adds header and normalises whitespace.

    Parameters
    ----------
    content_type : str
        Must be "culture_fact" or "heritage_fact" for header to be applied.
    generated_content : str
        Raw generated content (title + body).

    Returns
    -------
    str
        Content unchanged if content_type not in (culture_fact, heritage_fact);
        otherwise HEADER + "\\n\\n" + title_line + "\\n" + "\\n".join(body_lines), normalised.
    """
    if content_type not in ("culture_fact", "heritage_fact"):
        return generated_content

    header = _HEADERS.get(content_type)
    if not header:
        return generated_content

    normalised = _normalise_input(generated_content or "")
    if not normalised:
        return generated_content

    lines = normalised.split("\n")
    # First non-empty line = title (or existing header; then next non-empty = title for idempotency)
    title_line = None
    title_idx = None
    for idx, line in enumerate(lines):
        if line.strip():
            first_line = line.strip()
            # Idempotency: if first non-empty line is already the correct header, use next non-empty as title
            if first_line == header:
                continue
            title_line = line
            title_idx = idx
            break
    if title_line is None or title_idx is None:
        return generated_content
    body_lines = lines[title_idx + 1:]

    # A3: HEADER + "\n\n" + title_line + "\n" + "\n".join(body_lines)
    built = header + "\n\n" + title_line + "\n" + "\n".join(body_lines)
    return _normalise_output(built)
