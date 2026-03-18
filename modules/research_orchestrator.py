from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Any, Dict, List, Optional, Tuple

from config.database import db_manager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResearchOrchestrator:
    """
    Domain 2 (Library): Minimal research readiness gate.

    Contract:
    - If the post has no research substage rows, treat research as not required (ready=True).
    - If research substage rows exist, require a "complete" status.
    """

    complete_statuses: tuple[str, ...] = (
        "research_complete",
        "complete",
        "completed",
        "done",
        "ready",
    )

    def is_research_ready(self, post_id: int) -> bool:
        if not isinstance(post_id, int) or post_id <= 0:
            return False

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pws.status, wsse.name AS substage_name
                    FROM post_workflow_sub_stage pws
                    JOIN workflow_sub_stage_entity wsse ON wsse.id = pws.sub_stage_id
                    WHERE pws.post_id = %s
                      AND wsse.name ILIKE '%%research%%'
                    """,
                    (post_id,),
                )
                rows = cursor.fetchall() or []
        except Exception as e:
            logger.warning("Research readiness check failed for post_id=%s: %s", post_id, e)
            return False

        # No research substages attached => no requirement.
        if not rows:
            return True

        for r in rows:
            status = (r.get("status") if isinstance(r, dict) else None) or ""
            if status.strip().lower() in self.complete_statuses:
                return True

        return False

    def fetch_internal_intelligence(self, surname: str, *, limit_kb: int = 5, limit_chunks: int = 8) -> Dict[str, Any]:
        """
        Domain 2 (Library): Clan-First internal intelligence.

        Contract:
        - SQL full-text search against `clan_kb_articles` (uses idx_clan_kb_articles_text_fts)
        - FAISS semantic chunks via `ContentRetriever` (from `content_chunks`)
        - Privileged Clan.com product links via `clan_products` + tartan-design CSV mapping
        """
        surname = (surname or "").strip()
        if not surname:
            return {"success": False, "error": "Missing surname", "found_internal_data": False}

        kb_hits: List[Dict[str, Any]] = []
        semantic_chunks: List[Dict[str, Any]] = []
        privileged_links: List[Dict[str, Any]] = []

        # 1) SQL: full-text on clan_kb_articles.text
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    WITH q AS (
                        SELECT plainto_tsquery('english', %s) AS query
                    )
                    SELECT
                        a.id,
                        a.category_id,
                        a.name,
                        a.url_key,
                        a.short_text,
                        ts_rank_cd(to_tsvector('english', a.text), q.query) AS rank
                    FROM clan_kb_articles a, q
                    WHERE a.is_active = TRUE
                      AND to_tsvector('english', a.text) @@ q.query
                    ORDER BY rank DESC
                    LIMIT %s
                    """,
                    (surname, limit_kb),
                )
                kb_hits = cursor.fetchall() or []
        except Exception as e:
            logger.warning("KB full-text search failed for surname=%s: %s", surname, e)

        # 2) FAISS: semantic chunks (FAISS backed via ContentRetriever)
        try:
            from utils.vector_search.retrieval import ContentRetriever

            retriever = ContentRetriever()
            faiss_result = retriever.search(
                query=surname,
                chunk_types=["kb"],
                limit=limit_chunks,
            )
            if faiss_result.get("success"):
                semantic_chunks = faiss_result.get("results", []) or []
        except Exception as e:
            logger.warning("FAISS retrieval failed for surname=%s: %s", surname, e)

        # 3) Privileged links: clan_products + tartan-design CSV mapping
        try:
            links_result = self.get_privileged_links(surname)
            privileged_links = links_result.get("links", []) or []
        except Exception as e:
            logger.warning("Privileged link resolution failed for surname=%s: %s", surname, e)

        found_internal_data = bool(kb_hits or semantic_chunks or privileged_links)

        primary_truth_text = self._build_primary_truth_text(
            surname=surname,
            kb_hits=kb_hits,
            semantic_chunks=semantic_chunks,
            privileged_links=privileged_links,
        )

        return {
            "success": True,
            "surname": surname,
            "found_internal_data": found_internal_data,
            "kb_hits": kb_hits,
            "semantic_chunks": semantic_chunks,
            "privileged_links": privileged_links,
            "primary_truth_text": primary_truth_text,
        }

    def _build_primary_truth_text(
        self,
        *,
        surname: str,
        kb_hits: List[Dict[str, Any]],
        semantic_chunks: List[Dict[str, Any]],
        privileged_links: List[Dict[str, Any]],
        max_chunk_chars: int = 1400,
        max_link_count: int = 8,
    ) -> str:
        """Small, deterministic summary string intended for LLM 'Primary Truth' injection."""
        parts: List[str] = []
        parts.append("=== PRIMARY TRUTH (INTERNAL - Clan-First) ===")
        parts.append(f"Surname token: {surname}")

        if kb_hits:
            parts.append("")
            parts.append("KB full-text hits (clan_kb_articles):")
            for i, hit in enumerate(kb_hits[:5], start=1):
                name = hit.get("name") or "N/A"
                url_key = hit.get("url_key") or ""
                short_text = (hit.get("short_text") or "").strip().replace("\n", " ")
                parts.append(f"{i}. {name} (url_key={url_key})")
                if short_text:
                    parts.append(f"   - {short_text[:260]}{'…' if len(short_text) > 260 else ''}")
        else:
            parts.append("")
            parts.append("KB full-text hits: none")

        if semantic_chunks:
            parts.append("")
            parts.append("FAISS semantic chunks (content_chunks where chunk_type='kb'):")
            for i, ch in enumerate(semantic_chunks[:6], start=1):
                meta = ch.get("metadata") or {}
                score = ch.get("score")
                chunk_text = (ch.get("chunk_text") or "").strip().replace("\n", " ")
                chunk_text = chunk_text[: max_chunk_chars // 6] if chunk_text else ""
                parts.append(f"{i}. chunk_id={ch.get('chunk_id')} score={score}")
                if chunk_text:
                    parts.append(f"   - {chunk_text}{'…' if len(chunk_text) >= max_chunk_chars // 6 else ''}")
                if meta:
                    parts.append(f"   - metadata keys: {', '.join(sorted(meta.keys())[:6])}")
        else:
            parts.append("")
            parts.append("FAISS semantic chunks: none")

        if privileged_links:
            parts.append("")
            parts.append("Privileged Clan.com links (from clan_products + tartan CSV mapping):")
            for i, link in enumerate(privileged_links[:max_link_count], start=1):
                parts.append(
                    f"{i}. {link.get('name') or 'N/A'} :: url={link.get('url') or ''}"
                )
        else:
            parts.append("")
            parts.append("Privileged Clan.com links: none")

        parts.append("")
        parts.append("Rule: If you cite or reference heritage claims, prefer KB hits and privileged links above.")
        return "\n".join(parts)

    def get_privileged_links(self, surname: str) -> Dict[str, Any]:
        """
        Resolve 'Privileged Links' for Family/Profile research.

        Approach:
        - Use tartan-design CSVs to derive candidate clan legacy_ids for the surname.
        - Query `clan_products` for canonical Clan.com product URLs where:
            1) product name/url matches the surname, and/or
            2) clan_products.additional_data text contains the legacy_id token(s).
        """
        surname = (surname or "").strip()
        if not surname:
            return {"success": False, "error": "Missing surname", "links": []}

        legacy_ids = self._get_tartan_legacy_ids_for_surname(surname, max_legacy_ids=8)

        links: List[Dict[str, Any]] = []
        seen_urls: set[str] = set()

        # Primary: direct match against clan_products.name/url
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, url, image_url
                    FROM clan_products
                    WHERE (name ILIKE %s OR url ILIKE %s)
                    ORDER BY clan_updated_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    (f"%{surname}%", f"%{surname}%", 10),
                )
                rows = cursor.fetchall() or []
                for r in rows:
                    url = (r.get("url") or "").strip()
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        links.append(dict(r))
        except Exception as e:
            logger.warning("clan_products direct match failed for surname=%s: %s", surname, e)

        # Secondary: match legacy_id tokens inside additional_data JSONB
        try:
            if legacy_ids:
                with db_manager.get_cursor() as cursor:
                    for legacy_id in legacy_ids[:5]:
                        cursor.execute(
                            """
                            SELECT id, name, url, image_url
                            FROM clan_products
                            WHERE additional_data::text ILIKE %s
                            LIMIT %s
                            """,
                            (f"%{legacy_id}%", 8),
                        )
                        rows = cursor.fetchall() or []
                        for r in rows:
                            url = (r.get("url") or "").strip()
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                links.append(dict(r))
        except Exception as e:
            logger.warning("clan_products legacy_id match failed for surname=%s: %s", surname, e)

        return {"success": True, "surname": surname, "legacy_ids_used": legacy_ids, "links": links}

    def _get_tartan_legacy_ids_for_surname(self, surname: str, *, max_legacy_ids: int = 8) -> List[str]:
        """Extract candidate legacy_ids from tartan-design CSV for use in clan_products additional_data matching."""
        surname_lower = surname.lower()
        csv_path = (
            Path(__file__).resolve().parent.parent
            / "side-projects"
            / "tartan-design"
            / "data"
            / "tartan_designs_clan_full.csv"
        )
        legacy_ids: List[str] = []
        if not csv_path.exists():
            logger.warning("tartan-design CSV not found: %s", csv_path)
            return legacy_ids

        try:
            with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    family = (row.get("family") or "").strip()
                    if family.lower() != surname_lower:
                        continue

                    legacy_id = (row.get("legacy_id") or "").strip()
                    if not legacy_id or legacy_id.lower() == "none":
                        continue

                    if legacy_id not in legacy_ids:
                        legacy_ids.append(legacy_id)
                        if len(legacy_ids) >= max_legacy_ids:
                            break
        except Exception as e:
            logger.warning("Failed reading tartan-design CSV for surname=%s: %s", surname, e)

        return legacy_ids

