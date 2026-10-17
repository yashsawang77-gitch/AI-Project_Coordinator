"""
Syncora AI - LLM Provider Abstraction & Natural Language Progress Engine
Supports Google Gemini, OpenAI, and a robust deterministic offline fallback.
Never executes arbitrary SQL or directly modifies the database.
Outputs are strictly validated against Pydantic schemas.
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import httpx
from pydantic import BaseModel, Field
from config import settings

logger = logging.getLogger("llm_provider")

# ==============================================================================
# Pydantic Schemas for Strict Output Validation
# ==============================================================================
class LLMProgressInterpretation(BaseModel):
    task_id: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    status: str = Field(default="In Progress", description="Pending, In Progress, Blocked, or Completed")
    summary: Optional[str] = None
    completed_work: Optional[str] = None
    remaining_work: Optional[str] = None
    blocker_description: Optional[str] = None
    proposed_deadline: Optional[str] = None
    clarification_required: bool = False
    clarification_prompt: Optional[str] = None
    suggested_next_action: Optional[str] = None
    confidence: int = Field(default=85, ge=0, le=100)
    evidence: str
    metadata_provenance: Dict[str, Any] = Field(default_factory=dict)

class LLMEffortEstimate(BaseModel):
    min_estimated_hours: float = Field(ge=0.5)
    max_estimated_hours: float = Field(ge=0.5)
    assumptions: List[str] = Field(default_factory=list)
    confidence_level: str = Field(default="Medium", description="High, Medium, or Low")
    information_needed: List[str] = Field(default_factory=list)
    is_ai_estimate: bool = True

# ==============================================================================
# Provider Interface
# ==============================================================================
class BaseLLMProvider(ABC):
    @abstractmethod
    async def interpret_progress(
        self,
        text: str,
        member_id: str,
        candidate_tasks: List[Any],
        recent_context: Optional[str] = None
    ) -> LLMProgressInterpretation:
        """Parses natural language update and returns validated structured interpretation."""
        pass

    @abstractmethod
    async def estimate_effort(
        self,
        task_title: str,
        task_description: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> LLMEffortEstimate:
        """Suggests estimated effort hours range with assumptions and uncertainty disclosure."""
        pass

# ==============================================================================
# Mock / Deterministic Rule-Based Provider (Offline / Hackathon Demo Fallback)
# ==============================================================================
class MockDeterministicLLMProvider(BaseLLMProvider):
    def parse_progress_sync(
        self,
        text: str,
        member_id: str,
        candidate_tasks: List[Any],
        recent_context: Optional[str] = None
    ) -> LLMProgressInterpretation:
        raw_text = text.strip()
        lower_text = raw_text.lower()

        # 1. Resolve Task ID
        task_id = None
        # Explicit ID match (e.g. SYNC-201)
        id_match = re.search(r"SYNC-\d+", raw_text.upper())
        if id_match:
            task_id = id_match.group(0)
        else:
            # Check recent active reminder
            from database import get_db_connection
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT task_id FROM reminders 
                    WHERE member_id = ? AND replied = 0
                    ORDER BY sent_at DESC LIMIT 1
                """, (member_id,))
                rem_row = cursor.fetchone()
                conn.close()
                if rem_row:
                    task_id = rem_row["task_id"]
            except Exception:
                pass

        if not task_id:
            # Keyword matching on task titles
            clean_words = set(re.findall(r"\w{4,}", lower_text))
            matches = []
            for t in candidate_tasks:
                t_words = set(re.findall(r"\w{4,}", t.title.lower()))
                common = clean_words.intersection(t_words)
                if common:
                    matches.append((len(common), t))
            if matches:
                matches.sort(key=lambda x: x[0], reverse=True)
                if len(matches) == 1 or matches[0][0] > matches[1][0]:
                    task_id = matches[0][1].id

        active_tasks = [t for t in candidate_tasks if getattr(t, 'status', '') != 'Completed']
        if not task_id and len(active_tasks) == 1:
            task_id = active_tasks[0].id

        # Ambiguity check
        if not task_id and len(active_tasks) > 1:
            options = ", ".join([f"{t.id} ({t.title})" for t in active_tasks[:3]])
            return LLMProgressInterpretation(
                task_id=None,
                progress_percentage=None,
                status="In Progress",
                clarification_required=True,
                clarification_prompt=f"Which task is this update for? You have: {options}. Please reply with the task ID.",
                confidence=40,
                evidence=raw_text,
                metadata_provenance={
                    "actual_evidence": raw_text,
                    "calculated_metrics": {"progress_num": None, "target_status": None},
                    "ai_estimates": {"confidence_score": "40%", "inferred_blocker": False}
                }
            )

        # 2. Extract completed work & remaining work
        completed_work = None
        remaining_work = None
        if "completed the" in lower_text:
            m = re.search(r"completed the\s+([^,.;]+)", lower_text)
            if m:
                completed_work = m.group(1).strip()
        elif "is done" in lower_text or "done" in lower_text:
            m = re.search(r"(?:the\s+)?([^,.;]+)\s+is done", lower_text)
            if m:
                completed_work = m.group(1).strip()

        if "is pending" in lower_text:
            m = re.search(r"([^,.;]+)\s+is pending", lower_text)
            if m:
                subj = m.group(1).replace("but ", "").replace("the ", "").strip()
                remaining_work = subj
        elif "failing" in lower_text:
            m = re.search(r"([^,.;]+)\s+is failing", lower_text)
            if m:
                subj = m.group(1).replace("but ", "").replace("the ", "").strip()
                remaining_work = f"{subj} is failing"
        elif "finish" in lower_text:
            m = re.search(r"finish\s+([a-zA-Z_-]+)", lower_text)
            if m and m.group(1).lower() not in ("tomorrow", "today", "it", "this", "the", "a"):
                remaining_work = m.group(1).strip()

        # 3. Detect Blocker
        blocker_desc = None
        suggested_action = None
        is_blocked = False
        blocker_indicators = [
            ("can't continue until", r"can't continue until\s+([^,.;]+)"),
            ("cannot continue until", r"cannot continue until\s+([^,.;]+)"),
            ("waiting on", r"waiting on\s+([^,.;]+)"),
            ("waiting for", r"waiting for\s+([^,.;]+)"),
            ("blocked on", r"blocked on\s+([^,.;]+)"),
            ("is failing", r"(?:the\s+)?([^,.;]+ is failing)"),
        ]
        for phrase, pattern in blocker_indicators:
            if phrase in lower_text:
                is_blocked = True
                bm = re.search(pattern, lower_text)
                if bm:
                    blocker_desc = f"Waiting for {bm.group(1).strip()}" if "until" in phrase else bm.group(0).strip()
                else:
                    blocker_desc = f"Blocker reported: '{raw_text}'"
                break

        if is_blocked:
            # Infer suggested action
            if "dataset" in lower_text:
                suggested_action = "Follow up on dataset delivery and verify format specifications"
            elif "api" in lower_text or "webhook" in lower_text:
                suggested_action = "Check API gateway logs and verify credential tokens"
            else:
                suggested_action = "Alert project lead for impediment clearance"

        # 4. Proposed Deadline extraction
        proposed_deadline = None
        if "tomorrow" in lower_text:
            proposed_deadline = "Tomorrow"
        elif "next week" in lower_text:
            proposed_deadline = "Next Week"
        elif "friday" in lower_text:
            proposed_deadline = "Friday"

        # 5. Extract Progress Percentage
        progress_pct = None
        pct_match = re.search(r"(\d{1,3})\s*%", raw_text)
        if pct_match:
            val = int(pct_match.group(1))
            if 0 <= val <= 100:
                progress_pct = val

        # 6. Status Determination with Strict Guardrails
        # RULE: Do not mark complete merely because participant says "almost done"
        is_almost_done = any(p in lower_text for p in ["almost done", "nearly done", "almost finished", "just wrapping up"])
        if is_blocked:
            status = "Blocked"
            confidence = 94
        elif is_almost_done:
            status = "In Progress"
            progress_pct = progress_pct or 90
            remaining_work = remaining_work or "Final testing and review"
            confidence = 91
        elif progress_pct is not None:
            if progress_pct >= 100:
                status = "Completed"
                confidence = 98
            else:
                status = "In Progress"
                confidence = 92
        elif (
            ("completed" in lower_text or "all done" in lower_text or "shipped" in lower_text or "merged" in lower_text)
            and not remaining_work
            and not is_blocked
        ):
            status = "Completed"
            progress_pct = 100
            confidence = 96
        else:
            status = "In Progress"
            confidence = 88

        summary_parts = [f"Status: {status}."]
        if completed_work:
            summary_parts.append(f"Completed: {completed_work}.")
        if remaining_work:
            summary_parts.append(f"Remaining: {remaining_work}.")
        if blocker_desc:
            summary_parts.append(f"Blocker: {blocker_desc}.")
        if proposed_deadline:
            summary_parts.append(f"Target: {proposed_deadline}.")
        summary = " ".join(summary_parts)

        return LLMProgressInterpretation(
            task_id=task_id,
            progress_percentage=progress_pct,
            status=status,
            summary=summary,
            completed_work=completed_work,
            remaining_work=remaining_work,
            blocker_description=blocker_desc,
            proposed_deadline=proposed_deadline,
            clarification_required=False,
            clarification_prompt=None,
            suggested_next_action=suggested_action,
            confidence=confidence,
            evidence=raw_text,
            metadata_provenance={
                "actual_evidence": raw_text,
                "calculated_metrics": {
                    "progress_num": progress_pct,
                    "target_status": status,
                    "completed_work": completed_work,
                    "remaining_work": remaining_work,
                    "proposed_deadline": proposed_deadline,
                },
                "ai_estimates": {
                    "confidence_score": f"{confidence}%",
                    "inferred_blocker": is_blocked,
                    "suggested_next_action": suggested_action,
                }
            }
        )

    async def interpret_progress(
        self,
        text: str,
        member_id: str,
        candidate_tasks: List[Any],
        recent_context: Optional[str] = None
    ) -> LLMProgressInterpretation:
        return self.parse_progress_sync(text, member_id, candidate_tasks, recent_context)

    def estimate_effort_sync(
        self,
        task_title: str,
        task_description: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> LLMEffortEstimate:
        """Deterministic heuristic effort estimation."""
        combined_text = f"{task_title} {task_description} {' '.join(subtasks or [])}".lower()
        subtask_count = len(subtasks or [])
        dep_count = len(dependencies or [])

        # Heuristic base effort
        base_hours = 6.0
        if "webhook" in combined_text or "payment" in combined_text or "infrastructure" in combined_text:
            base_hours += 6.0
        if "dashboard" in combined_text or "analytics" in combined_text or "chart" in combined_text:
            base_hours += 5.0
        if "document" in combined_text or "copy" in combined_text:
            base_hours = 4.0

        base_hours += subtask_count * 2.5
        base_hours += dep_count * 3.0

        min_hours = round(max(2.0, base_hours * 0.75), 1)
        max_hours = round(base_hours * 1.35, 1)

        assumptions = [
            f"Scope involves {subtask_count} subtasks and {dep_count} external dependencies.",
            "Assumes continuous developer focus without third-party API outages."
        ]
        info_needed = []
        if dep_count > 0:
            info_needed.append("API sandbox access credentials and staging environment verification.")
        if not task_description:
            info_needed.append("Detailed acceptance criteria and UI wireframes.")

        return LLMEffortEstimate(
            min_estimated_hours=min_hours,
            max_estimated_hours=max_hours,
            assumptions=assumptions,
            confidence_level="High" if subtask_count > 0 else "Medium",
            information_needed=info_needed,
            is_ai_estimate=True
        )

    async def estimate_effort(
        self,
        task_title: str,
        task_description: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> LLMEffortEstimate:
        return self.estimate_effort_sync(task_title, task_description, subtasks, dependencies)

# ==============================================================================
# Google Gemini Provider
# ==============================================================================
class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        self.fallback = MockDeterministicLLMProvider()

    async def interpret_progress(
        self,
        text: str,
        member_id: str,
        candidate_tasks: List[Any],
        recent_context: Optional[str] = None
    ) -> LLMProgressInterpretation:
        tasks_brief = [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority} for t in candidate_tasks]
        prompt = (
            f"You are the AI Project Coordinator for high-velocity software teams.\n"
            f"Participant (Member ID: {member_id}) sent: \"{text}\".\n"
            f"Assigned Candidate Tasks: {json.dumps(tasks_brief)}.\n"
            f"Recent Context: {recent_context or 'None'}.\n\n"
            f"CRITICAL RULES:\n"
            f"1. Never mark status as 'Completed' merely because the user says 'almost done' or 'nearly finished'. Use 'In Progress'.\n"
            f"2. Only mark 'Completed' if they explicitly finished all work (100%, done, merged).\n"
            f"3. If external blockers exist (e.g. waiting for someone else, failing tests), set status='Blocked'.\n"
            f"4. Output strictly a JSON object adhering to this schema:\n"
            f"{{\n"
            f"  \"task_id\": \"string or null if ambiguous\",\n"
            f"  \"progress_percentage\": integer_or_null,\n"
            f"  \"status\": \"Pending\" | \"In Progress\" | \"Blocked\" | \"Completed\",\n"
            f"  \"completed_work\": \"string or null\",\n"
            f"  \"remaining_work\": \"string or null\",\n"
            f"  \"blocker_description\": \"string or null\",\n"
            f"  \"proposed_deadline\": \"string or null\",\n"
            f"  \"clarification_required\": boolean,\n"
            f"  \"clarification_prompt\": \"string or null\",\n"
            f"  \"suggested_next_action\": \"string or null\",\n"
            f"  \"confidence\": integer_0_to_100,\n"
            f"  \"evidence\": \"exact quote from text\"\n"
            f"}}"
        )
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(self.url, json=payload)
                if res.status_code == 200:
                    raw_json = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_json)
                    data["metadata_provenance"] = {
                        "actual_evidence": data.get("evidence", text),
                        "calculated_metrics": {
                            "progress_num": data.get("progress_percentage"),
                            "target_status": data.get("status")
                        },
                        "ai_estimates": {
                            "confidence_score": f"{data.get('confidence', 90)}%",
                            "inferred_blocker": bool(data.get("blocker_description"))
                        }
                    }
                    return LLMProgressInterpretation(**data)
        except Exception as e:
            logger.warning(f"Gemini interpretation failed: {e}. Falling back to deterministic NLP.")

        return await self.fallback.interpret_progress(text, member_id, candidate_tasks, recent_context)

    async def estimate_effort(
        self,
        task_title: str,
        task_description: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> LLMEffortEstimate:
        prompt = (
            f"Estimate software effort hours for this task:\n"
            f"Title: {task_title}\n"
            f"Description: {task_description}\n"
            f"Subtasks: {json.dumps(subtasks or [])}\n"
            f"Dependencies: {json.dumps(dependencies or [])}\n\n"
            f"Respond strictly in JSON:\n"
            f"{{\n"
            f"  \"min_estimated_hours\": float,\n"
            f"  \"max_estimated_hours\": float,\n"
            f"  \"assumptions\": [\"string\"],\n"
            f"  \"confidence_level\": \"High\" | \"Medium\" | \"Low\",\n"
            f"  \"information_needed\": [\"string\"],\n"
            f"  \"is_ai_estimate\": true\n"
            f"}}"
        )
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(self.url, json=payload)
                if res.status_code == 200:
                    raw_json = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_json)
                    return LLMEffortEstimate(**data)
        except Exception as e:
            logger.warning(f"Gemini effort estimation failed: {e}. Falling back to deterministic engine.")

        return await self.fallback.estimate_effort(task_title, task_description, subtasks, dependencies)

# ==============================================================================
# OpenAI Provider
# ==============================================================================
class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.fallback = MockDeterministicLLMProvider()

    async def interpret_progress(
        self,
        text: str,
        member_id: str,
        candidate_tasks: List[Any],
        recent_context: Optional[str] = None
    ) -> LLMProgressInterpretation:
        tasks_brief = [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority} for t in candidate_tasks]
        prompt = (
            f"You are the AI Project Coordinator.\n"
            f"Participant: {member_id}\n"
            f"Message: \"{text}\"\n"
            f"Tasks: {json.dumps(tasks_brief)}\n"
            f"Never mark complete if user says 'almost done'.\n"
            f"Output JSON with keys: task_id, progress_percentage, status, completed_work, remaining_work, blocker_description, proposed_deadline, clarification_required, clarification_prompt, suggested_next_action, confidence, evidence."
        )
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = json.loads(res.json()["choices"][0]["message"]["content"])
                    data["metadata_provenance"] = {
                        "actual_evidence": data.get("evidence", text),
                        "calculated_metrics": {
                            "progress_num": data.get("progress_percentage"),
                            "target_status": data.get("status")
                        },
                        "ai_estimates": {
                            "confidence_score": f"{data.get('confidence', 90)}%",
                            "inferred_blocker": bool(data.get("blocker_description"))
                        }
                    }
                    return LLMProgressInterpretation(**data)
        except Exception as e:
            logger.warning(f"OpenAI interpretation failed: {e}. Falling back to deterministic NLP.")

        return await self.fallback.interpret_progress(text, member_id, candidate_tasks, recent_context)

    async def estimate_effort(
        self,
        task_title: str,
        task_description: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> LLMEffortEstimate:
        prompt = (
            f"Estimate effort hours in JSON with min_estimated_hours, max_estimated_hours, assumptions, confidence_level, information_needed, is_ai_estimate: true for task '{task_title}': {task_description}."
        )
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = json.loads(res.json()["choices"][0]["message"]["content"])
                    return LLMEffortEstimate(**data)
        except Exception as e:
            logger.warning(f"OpenAI effort estimation failed: {e}. Falling back to deterministic engine.")

        return await self.fallback.estimate_effort(task_title, task_description, subtasks, dependencies)

# ==============================================================================
# Factory Function
# ==============================================================================
def get_llm_provider() -> BaseLLMProvider:
    """Factory selecting the active LLM provider based on environment configuration."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        return GeminiLLMProvider(settings.GEMINI_API_KEY.strip())
    elif settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        return OpenAILLMProvider(settings.OPENAI_API_KEY.strip())
    return MockDeterministicLLMProvider()
