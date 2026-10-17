"""
Syncora AI - AI Message Interpretation Service
Interprets natural language updates from Telegram and web chat, extracts evidence,
identifies relevant tasks, detects blockers, and provides confidence scores.
Integrates with LLM provider abstraction (Google Gemini, OpenAI, or MockDeterministic).
Strictly adheres to data provenance:
  1. Actual Information (directly stated by the human participant)
  2. Calculated Metrics (algorithmically determined from status/hours)
  3. AI-Generated Estimates (confidence and latent risk inference)
"""

import re
import json
import logging
from typing import Optional, Dict, Any, List
import asyncio
from config import settings
from models.schemas import TaskModel
from services.task_service import TaskService
from services.llm_provider import get_llm_provider, MockDeterministicLLMProvider, LLMProgressInterpretation

logger = logging.getLogger("ai_interpreter")

class InterpretationResult:
    def __init__(
        self,
        task_id: Optional[str],
        progress_percentage: Optional[int],
        status_change: Optional[str],
        is_blocked: bool,
        blocker_reason: Optional[str],
        blocker_urgency: str,
        confidence: int,
        summary: str,
        evidence: str,
        clarification_needed: bool = False,
        clarification_prompt: Optional[str] = None,
        completed_work: Optional[str] = None,
        remaining_work: Optional[str] = None,
        proposed_deadline: Optional[str] = None,
        suggested_next_action: Optional[str] = None,
    ):
        self.task_id = task_id
        self.progress_percentage = progress_percentage
        self.status_change = status_change
        self.is_blocked = is_blocked
        self.blocker_reason = blocker_reason
        self.blocker_urgency = blocker_urgency
        self.confidence = confidence
        self.summary = summary
        self.evidence = evidence
        self.clarification_needed = clarification_needed
        self.clarification_prompt = clarification_prompt
        self.completed_work = completed_work
        self.remaining_work = remaining_work
        self.proposed_deadline = proposed_deadline
        self.suggested_next_action = suggested_next_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "progress_percentage": self.progress_percentage,
            "status_change": self.status_change,
            "is_blocked": self.is_blocked,
            "blocker_reason": self.blocker_reason,
            "blocker_urgency": self.blocker_urgency,
            "confidence": f"{self.confidence}%" if isinstance(self.confidence, int) else str(self.confidence),
            "summary": self.summary,
            "evidence": self.evidence,
            "clarification_needed": self.clarification_needed,
            "clarification_prompt": self.clarification_prompt,
            "completed_work": self.completed_work,
            "remaining_work": self.remaining_work,
            "proposed_deadline": self.proposed_deadline,
            "suggested_next_action": self.suggested_next_action,
            "metadata_provenance": {
                "actual_evidence": self.evidence,
                "calculated_metrics": {
                    "progress_num": self.progress_percentage,
                    "target_status": self.status_change,
                    "completed_work": self.completed_work,
                    "remaining_work": self.remaining_work,
                    "proposed_deadline": self.proposed_deadline,
                },
                "ai_estimates": {
                    "confidence_score": f"{self.confidence}%" if isinstance(self.confidence, int) else str(self.confidence),
                    "inferred_blocker": self.is_blocked,
                    "suggested_next_action": self.suggested_next_action,
                }
            }
        }


class AIInterpreterService:
    @classmethod
    def resolve_task_for_message(
        cls, member_id: str, message_text: str, candidate_tasks: List[TaskModel]
    ) -> Optional[TaskModel]:
        """
        Identifies the relevant task using:
        1. Explicit task ID in message (e.g., SYNC-201).
        2. Recent unreplied reminder association.
        3. Keyword title match among member's assigned tasks.
        4. Single active task default.
        5. Rejects ambiguous references when multiple tasks match equally.
        """
        text_upper = message_text.upper()

        # 1. Explicit ID match
        id_match = re.search(r"SYNC-\d+", text_upper)
        if id_match:
            explicit_id = id_match.group(0)
            for t in candidate_tasks:
                if t.id.upper() == explicit_id:
                    return t
            global_task = TaskService.get_task_by_id(explicit_id)
            if global_task:
                return global_task

        # 2. Check for active unreplied reminder for this member
        try:
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id FROM reminders 
                WHERE member_id = ? AND replied = 0
                ORDER BY sent_at DESC LIMIT 1
            """, (member_id,))
            reminder_row = cursor.fetchone()
            conn.close()

            if reminder_row:
                reminded_task_id = reminder_row["task_id"]
                for t in candidate_tasks:
                    if t.id.upper() == reminded_task_id.upper():
                        return t
                global_task = TaskService.get_task_by_id(reminded_task_id)
                if global_task:
                    return global_task
        except Exception:
            pass

        # 3. Keyword matching on candidate task titles
        matches = []
        clean_text_words = set(re.findall(r"\w{4,}", message_text.lower()))
        for t in candidate_tasks:
            title_words = set(re.findall(r"\w{4,}", t.title.lower()))
            common = clean_text_words.intersection(title_words)
            if len(common) >= 1:
                matches.append((len(common), t))

        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            if len(matches) == 1 or matches[0][0] > matches[1][0]:
                return matches[0][1]

        # 4. If member only has 1 active task
        active_tasks = [t for t in candidate_tasks if t.status != "Completed"]
        if len(active_tasks) == 1:
            return active_tasks[0]

        return None

    @classmethod
    def _llm_res_to_interpretation(
        cls, llm_res: LLMProgressInterpretation, raw_text: str
    ) -> InterpretationResult:
        urgency = "Normal"
        if llm_res.status == "Blocked" or llm_res.blocker_description:
            urgency = "Critical" if ("critical" in raw_text.lower() or "urgent" in raw_text.lower() or "credentials" in raw_text.lower()) else "High"

        return InterpretationResult(
            task_id=llm_res.task_id,
            progress_percentage=llm_res.progress_percentage,
            status_change=llm_res.status,
            is_blocked=(llm_res.status == "Blocked" or bool(llm_res.blocker_description)),
            blocker_reason=llm_res.blocker_description,
            blocker_urgency=urgency,
            confidence=llm_res.confidence,
            summary=llm_res.summary or f"Status: {llm_res.status}.",
            evidence=llm_res.evidence or raw_text,
            clarification_needed=llm_res.clarification_required,
            clarification_prompt=llm_res.clarification_prompt,
            completed_work=llm_res.completed_work,
            remaining_work=llm_res.remaining_work,
            proposed_deadline=llm_res.proposed_deadline,
            suggested_next_action=llm_res.suggested_next_action,
        )

    @classmethod
    def interpret_message(
        cls, message_text: str, member_id: str, candidate_tasks: List[TaskModel]
    ) -> InterpretationResult:
        """
        Synchronously parses inbound messages using the deterministic offline rule engine.
        Guarantees instant response without blocking network threads.
        """
        provider = MockDeterministicLLMProvider()
        llm_res = provider.parse_progress_sync(message_text, member_id, candidate_tasks)
        return cls._llm_res_to_interpretation(llm_res, message_text)

    @classmethod
    async def interpret_message_async(
        cls, message_text: str, member_id: str, candidate_tasks: List[TaskModel]
    ) -> InterpretationResult:
        """
        Asynchronously parses inbound messages through the configured LLM provider
        (Google Gemini or OpenAI if API keys are set, otherwise MockDeterministicLLMProvider).
        Strictly validates model output against Pydantic schemas.
        """
        provider = get_llm_provider()
        llm_res = await provider.interpret_progress(message_text, member_id, candidate_tasks)
        return cls._llm_res_to_interpretation(llm_res, message_text)
