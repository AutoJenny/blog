"""
AUTHORITY_SHORT Content Generator (Facebook)

Phase 7: Generates short authority/context posts for Friday Matrix slots.

Design goals (v1):
- One post per Friday for Facebook, role = AUTHORITY_SHORT.
- Source text from rota topic (preferred) or fallback KB article.
- 200–400 character target (hard cap 600), 1–2 short paragraphs, factual tone.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Dict, Optional

from config.database import db_manager
from modules.llm_service import LLMService
from utils.content_roles.validator import ContentRoleValidator

logger = logging.getLogger(__name__)


class AuthorityShortGenerator:
    """
    Generates AUTHORITY_SHORT posts from KB rota topics and/or KB articles.

    Requirements (v1):
    - role = AUTHORITY_SHORT
    - platform = facebook
    - channel_type = feed_post
    - content_type = authority_short
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.validator = ContentRoleValidator()
        self.max_chars = 600  # hard cap
        self.target_min_chars = 200
        self.target_max_chars = 400

    # ---- public API -----------------------------------------------------

    def generate_for_friday(self, friday: date, posting_queue_id: int) -> Dict:
        """
        Generate AUTHORITY_SHORT content for a given Friday date.

        Returns dict:
          - success: bool
          - content: text (if success)
          - char_count: int
          - source_type: str
          - topic_id: Optional[int]
          - source_page_id: Optional[int]
          - validation_report_json: dict
          - error: str (if not success)
        """
        try:
            rota_info = self._get_rota_for_week(friday)
        except Exception as e:
            logger.error("Error getting rota for Friday %s: %s", friday, e, exc_info=True)
            rota_info = None

        topic_id = rota_info.get("topic_id") if rota_info else None
        rota_year = rota_info.get("year") if rota_info else None
        rota_week = rota_info.get("week") if rota_info else None

        source_text, source_type, source_page_id = self._select_source_text(topic_id)
        if not source_text:
            return {
                "success": False,
                "error": "No suitable source text found for AUTHORITY_SHORT",
                "topic_id": topic_id,
                "source_page_id": source_page_id,
            }

        # Call LLM with role-specific prompt, up to N attempts
        attempts = 0
        last_error: Optional[str] = None
        content: Optional[str] = None

        while attempts < 3:
            attempts += 1
            llm_result = self._call_llm_authority_short(
                source_text=source_text,
                topic_id=topic_id,
                source_page_id=source_page_id,
                rota_year=rota_year,
                rota_week=rota_week,
                posting_queue_id=posting_queue_id,
            )
            if "error" in llm_result:
                last_error = llm_result["error"]
                logger.warning(
                    "AUTHORITY_SHORT LLM attempt %s failed: %s", attempts, last_error
                )
                continue

            content = self._clean_and_trim_text(llm_result.get("content", ""))
            if not content:
                last_error = "LLM returned empty content"
                continue

            # For now, validator has no role-specific checks for AUTHORITY_SHORT,
            # but we still call it to get a structured report.
            validation = self.validator.validate(
                "AUTHORITY_SHORT", content, source_page_id=source_page_id
            )
            ok = validation.get("valid", True)

            # Basic hard constraints for this role
            char_count = len(content)
            if char_count < self.target_min_chars or char_count > self.max_chars:
                ok = False
                issues = validation.setdefault("validation_report_json", {}).setdefault(
                    "issues", []
                )
                issues.append(
                    f"Character count out of range: {char_count} "
                    f"(target {self.target_min_chars}-{self.target_max_chars}, max {self.max_chars})"
                )

            if ok:
                return {
                    "success": True,
                    "content": content,
                    "char_count": char_count,
                    "topic_id": topic_id,
                    "source_page_id": source_page_id,
                    "rota_year": rota_year,
                    "rota_week": rota_week,
                    "source_type": source_type,
                    "validation_report_json": validation.get(
                        "validation_report_json", {"valid": True, "role": "AUTHORITY_SHORT"}
                    ),
                }

            # validation failed; try again
            last_error = "; ".join(validation.get("issues", [])) or "Validation failed"

        # If all attempts failed
        return {
            "success": False,
            "error": last_error or "AUTHORITY_SHORT generation failed after retries",
            "topic_id": topic_id,
            "source_page_id": source_page_id,
            "rota_year": rota_year,
            "rota_week": rota_week,
        }

    # ---- source selection -----------------------------------------------

    def _get_rota_for_week(self, friday: date) -> Optional[Dict]:
        """Get rota entry (topic) for the ISO week containing Friday."""
        year, week, _ = friday.isocalendar()
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT r.id as rota_id,
                       r.topic_id,
                       r.scheduled_year,
                       r.scheduled_week,
                       r.scheduled_date
                FROM kb_topic_rota r
                WHERE r.scheduled_year = %s
                  AND r.scheduled_week = %s
                """,
                (year, week),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "rota_id": row["rota_id"],
            "topic_id": row["topic_id"],
            "year": row["scheduled_year"],
            "week": row["scheduled_week"],
            "scheduled_date": row["scheduled_date"],
        }

    def _select_source_text(self, topic_id: Optional[int]) -> (Optional[str], str, Optional[int]):
        """
        Select source text for AUTHORITY_SHORT.

        Strategy:
          1) If topic_id exists, try aggregated content for that topic (kb_topic_content).
          2) Fallback: first active KB article for topic (clan_kb_articles via kb_topics.article_ids).
          3) Final fallback: any active reference/article in clan_kb_articles.
        """
        # 1) Aggregated content for rota topic
        if topic_id:
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT aggregated_text, source_article_ids
                        FROM kb_topic_content
                        WHERE topic_id = %s
                        ORDER BY word_count DESC
                        LIMIT 1
                        """,
                        (topic_id,),
                    )
                    row = cursor.fetchone()
                if row and row["aggregated_text"]:
                    source_ids = row.get("source_article_ids") or []
                    first_source_id = source_ids[0] if source_ids else None
                    return row["aggregated_text"], "rota_topic", first_source_id
            except Exception as e:
                logger.warning(
                    "AUTHORITY_SHORT: error reading kb_topic_content for topic %s: %s",
                    topic_id,
                    e,
                )

            # 2) direct article from kb_topics.article_ids
            try:
                with db_manager.get_cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT article_ids
                        FROM kb_topics
                        WHERE id = %s AND is_active = TRUE
                        """,
                        (topic_id,),
                    )
                    topic_row = cursor.fetchone()
                if topic_row and topic_row["article_ids"]:
                    article_ids = topic_row["article_ids"]
                    source_page_id = article_ids[0]
                    text = self._fetch_article_excerpt(source_page_id)
                    if text:
                        return text, "rota_topic_article", source_page_id
            except Exception as e:
                logger.warning(
                    "AUTHORITY_SHORT: error reading kb_topics for topic %s: %s",
                    topic_id,
                    e,
                )

        # 3) generic fallback: any active article with substantial text
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM clan_kb_articles
                    WHERE is_active = TRUE
                    ORDER BY id ASC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
            if row:
                source_page_id = row["id"]
                text = self._fetch_article_excerpt(source_page_id)
                if text:
                    return text, "fallback_article", source_page_id
        except Exception as e:
            logger.error("AUTHORITY_SHORT: error selecting fallback article: %s", e)

        return None, "none", None

    def _fetch_article_excerpt(self, article_id: int) -> Optional[str]:
        """Fetch a bounded excerpt of article text from clan_kb_articles."""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT text
                    FROM clan_kb_articles
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (article_id,),
                )
                row = cursor.fetchone()
            if not row or not row["text"]:
                return None
            # For v1, just use raw HTML-stripped text up to a few kB; depth_long already has
            # a more complex HTML cleaner. Here we rely on the LLM to handle the style.
            html = row["text"]
            # Simple strip of tags; depth_long uses BeautifulSoup, but to avoid duplication
            # we keep this minimal and let the LLM summarise.
            import re

            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:4000]
        except Exception as e:
            logger.error(
                "AUTHORITY_SHORT: error fetching article %s: %s", article_id, e
            )
            return None

    # ---- LLM call -------------------------------------------------------

    def _call_llm_authority_short(
        self,
        source_text: str,
        topic_id: Optional[int],
        source_page_id: Optional[int],
        rota_year: Optional[int],
        rota_week: Optional[int],
        posting_queue_id: int,
    ) -> Dict:
        """
        Call LLMService (Ollama) to generate AUTHORITY_SHORT text from source_text.
        """
        system_prompt = (
            "You are generating a short AUTHORITY_SHORT Facebook post for a heritage shop. "
            "The role is AUTHORITY_SHORT: calm, factual, context-setting. "
            "No emojis, no hashtags, no calls to action. "
            "Length target 200–400 characters, hard cap 600. "
            "1–2 short paragraphs, plain text only."
        )
        user_prompt = (
            "Using the following source material, write a short authoritative statement "
            "about Scottish clans, tartan, or provenance. Do NOT sell anything, do not reassure, "
            "and do not ask the reader to do anything. Stick to one clear factual idea.\n\n"
            f"SOURCE:\n{source_text}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Match DEPTH_LONG: use local Ollama (llama3.2) for generation.
        provider = "ollama"
        model = "llama3.2:latest"

        # LLMService currently requires an intercept_context with post_id;
        # we provide a minimal context using the posting_queue_id.
        intercept_context = {
            "post_id": posting_queue_id,
            "role": "AUTHORITY_SHORT",
            "meta": {
                "topic_id": topic_id,
                "source_page_id": source_page_id,
                "rota_year": rota_year,
                "rota_week": rota_week,
            },
        }

        try:
            result = self.llm_service.execute_llm_request(
                provider=provider,
                model=model,
                messages=messages,
                api_key=None,
                intercept_context=intercept_context,
            )
            return result
        except Exception as e:
            logger.error("AUTHORITY_SHORT: LLM call failed: %s", e, exc_info=True)
            return {"error": str(e)}

    # ---- text cleanup ---------------------------------------------------

    def _clean_and_trim_text(self, content: str) -> str:
        """Normalize whitespace and enforce max length."""
        if not content:
            return ""
        text = content.strip()

        # Normalise newlines: collapse 3+ down to 2
        import re

        text = re.sub(r"\n{3,}", "\n\n", text)

        # Enforce hard char cap; prefer not to truncate but allowed as last resort
        if len(text) > self.max_chars:
            text = self._truncate_at_sentence_boundary(text, self.max_chars)
        return text

    def _truncate_at_sentence_boundary(self, text: str, max_chars: int) -> str:
        """Truncate text at or before max_chars, ideally at a sentence boundary."""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        # Try to backtrack to last period or newline within last 60 chars
        window = truncated[-60:]
        last_break = max(window.rfind("."), window.rfind("!"), window.rfind("?"))
        if last_break != -1:
            return truncated[: max_chars - (60 - last_break)].rstrip()
        return truncated.rstrip()

