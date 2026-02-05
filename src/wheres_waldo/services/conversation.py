"""Conversational investigation service for multi-turn visual analysis.

Enables follow-up questions like "Where exactly did the padding change?"
with targeted zoom-ins and annotations using Gemini agentic vision.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from wheres_waldo.models.domain import ComparisonResult
from wheres_waldo.services.gemini_integration import GeminiIntegrationService
from wheres_waldo.services.storage import StorageService
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class ConversationPattern(str, Enum):
    """Conversational UI investigation patterns."""

    ZOOM = "zoom"
    CROP = "crop"
    ANNOTATE = "annotate"
    MEASURE = "measure"
    COMPARE = "compare"


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""

    turn_number: int = Field(description="Turn number (1-based)")
    question: str = Field(description="User question")
    answer: str = Field(description="Gemini response")
    annotation_path: Path | None = Field(default=None, description="Path to annotated screenshot")
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationSession:
    """Multi-turn conversation session."""

    def __init__(
        self,
        session_id: str,
        comparison_result: ComparisonResult,
        max_turns: int = 5,
    ) -> None:
        """Initialize conversation session.

        Args:
            session_id: Unique session identifier
            comparison_result: Original comparison result
            max_turns: Maximum number of turns (default: 5)
        """
        self.session_id = session_id
        self.comparison_result = comparison_result
        self.max_turns = max_turns
        self.turns: list[ConversationTurn] = []
        self.created_at = datetime.now()
        self.is_active = True

    def add_turn(self, question: str, answer: str, annotation_path: Path | None = None) -> ConversationTurn:
        """Add a turn to the conversation.

        Args:
            question: User question
            answer: Gemini response
            annotation_path: Optional path to annotated screenshot

        Returns:
            Created conversation turn
        """
        turn_number = len(self.turns) + 1

        if turn_number > self.max_turns:
            self.is_active = False
            raise ValueError(f"Maximum turns ({self.max_turns}) exceeded")

        turn = ConversationTurn(
            turn_number=turn_number,
            question=question,
            answer=answer,
            annotation_path=annotation_path,
        )

        self.turns.append(turn)

        # Check if this was the last turn
        if turn_number >= self.max_turns:
            self.is_active = False
            logger.info(f"Session {self.session_id} reached max turns")

        return turn

    def get_context(self) -> dict[str, Any]:
        """Get conversation context for Gemini.

        Returns:
            Context dictionary with conversation history
        """
        return {
            "session_id": self.session_id,
            "comparison_result": {
                "before_path": str(self.comparison_result.before_path),
                "after_path": str(self.comparison_result.after_path),
                "threshold": self.comparison_result.threshold,
                "changed_pixels": self.comparison_result.changed_pixels,
                "changed_percentage": self.comparison_result.changed_percentage,
                "intended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                    }
                    for c in self.comparison_result.intended_changes
                ],
                "unintended_changes": [
                    {
                        "description": c.description,
                        "bbox": c.bbox,
                        "severity": c.severity.value if c.severity else None,
                    }
                    for c in self.comparison_result.unintended_changes
                ],
            },
            "turns": [
                {
                    "turn_number": t.turn_number,
                    "question": t.question,
                    "answer": t.answer,
                }
                for t in self.turns
            ],
            "current_turn": len(self.turns) + 1,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "max_turns": self.max_turns,
            "is_active": self.is_active,
            "turns": [
                {
                    "turn_number": t.turn_number,
                    "question": t.question,
                    "answer": t.answer,
                    "annotation_path": str(t.annotation_path) if t.annotation_path else None,
                    "timestamp": t.timestamp.isoformat(),
                }
                for t in self.turns
            ],
            "comparison_summary": {
                "before_path": str(self.comparison_result.before_path),
                "after_path": str(self.comparison_result.after_path),
                "changed_pixels": self.comparison_result.changed_pixels,
                "changed_percentage": self.comparison_result.changed_percentage,
            },
        }


class ConversationService:
    """Conversational investigation service.

    Enables multi-turn conversations about visual changes with
    targeted zoom-ins and annotations.
    """

    def __init__(
        self,
        gemini_service: GeminiIntegrationService,
        storage_service: StorageService | None = None,
        max_turns: int = 5,
    ) -> None:
        """Initialize conversation service.

        Args:
            gemini_service: Gemini integration service
            storage_service: Storage service (creates if None)
            max_turns: Maximum turns per conversation
        """
        self.gemini_service = gemini_service
        self.storage_service = storage_service or StorageService()
        self.max_turns = max_turns

        # In-memory session storage
        self._sessions: dict[str, ConversationSession] = {}

        logger.info(f"ConversationService initialized with max_turns={max_turns}")

    def create_session(
        self,
        session_id: str,
        comparison_result: ComparisonResult,
    ) -> ConversationSession:
        """Create a new conversation session.

        Args:
            session_id: Unique session identifier
            comparison_result: Original comparison result

        Returns:
            Created session
        """
        session = ConversationSession(
            session_id=session_id,
            comparison_result=comparison_result,
            max_turns=self.max_turns,
        )

        self._sessions[session_id] = session
        logger.info(f"Created conversation session: {session_id}")

        return session

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Get existing session.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        return self._sessions.get(session_id)

    async def ask_followup(
        self,
        session_id: str,
        question: str,
    ) -> dict[str, Any]:
        """Ask a follow-up question in a conversation.

        Args:
            session_id: Session identifier
            question: Follow-up question

        Returns:
            Response with answer and optional annotation

        Raises:
            ValueError: If session not found or inactive
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.is_active:
            return {
                "success": False,
                "error": f"Session is inactive (max turns: {session.max_turns})",
                "session_id": session_id,
            }

        logger.info(f"Follow-up question (turn {len(session.turns) + 1}): {question}")

        # Detect pattern
        pattern = self._detect_pattern(question)
        logger.debug(f"Detected pattern: {pattern.value if pattern else 'none'}")

        # Build prompt with context
        context = session.get_context()
        prompt = self._build_followup_prompt(question, context, pattern)

        # Call Gemini
        try:
            # Rate limit check
            from wheres_waldo.services.gemini_integration import GeminiRateLimiter

            if not await self.gemini_service.rate_limiter.acquire():
                return {
                    "success": False,
                    "error": "Rate limit timeout - please try again later",
                    "rate_limiter_status": self.gemini_service.get_rate_limiter_status(),
                }

            # Load images
            import cv2
            before_img = cv2.imread(str(session.comparison_result.before_path))
            after_img = cv2.imread(str(session.comparison_result.after_path))

            if before_img is None or after_img is None:
                raise ValueError("Cannot load comparison images")

            # Convert to PIL
            from PIL import Image
            before_pil = Image.fromarray(cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB))
            after_pil = Image.fromarray(cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB))

            # Call Gemini
            response = self.gemini_service.client.generate_content(
                [prompt, before_pil, after_pil],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )

            answer = response.text

            # TODO: Generate annotated screenshot if requested
            # This would require Gemini to generate image annotations
            annotation_path = None

            # Add turn to session
            turn = session.add_turn(question, answer, annotation_path)

            # Save session to disk
            self._save_session(session)

            return {
                "success": True,
                "session_id": session_id,
                "turn_number": turn.turn_number,
                "question": question,
                "answer": answer,
                "annotation_path": str(annotation_path) if annotation_path else None,
                "turns_remaining": session.max_turns - turn.turn_number,
            }

        except Exception as e:
            logger.exception(f"Follow-up question failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
            }

    def _detect_pattern(self, question: str) -> ConversationPattern | None:
        """Detect conversational pattern from question.

        Args:
            question: User question

        Returns:
            Detected pattern or None
        """
        question_lower = question.lower()

        # Pattern keywords
        patterns = {
            ConversationPattern.ZOOM: ["zoom", "zoom in", "zoom out", "closer", "magnify"],
            ConversationPattern.CROP: ["crop", "focus on", "only show", "just the"],
            ConversationPattern.ANNOTATE: ["annotate", "mark", "highlight", "circle", "arrow"],
            ConversationPattern.MEASURE: ["measure", "distance", "size", "width", "height", "how big", "how far"],
            ConversationPattern.COMPARE: ["compare", "difference between", "versus", "vs"],
        }

        for pattern, keywords in patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                return pattern

        return None

    def _build_followup_prompt(
        self,
        question: str,
        context: dict[str, Any],
        pattern: ConversationPattern | None,
    ) -> str:
        """Build prompt for follow-up question.

        Args:
            question: User question
            context: Conversation context
            pattern: Detected pattern

        Returns:
            Prompt string
        """
        base_prompt = f"""You are analyzing visual regression testing results. The user has a follow-up question.

**Comparison Context**:
- Before: {context['comparison_result']['before_path']}
- After: {context['comparison_result']['after_path']}
- Changed Pixels: {context['comparison_result']['changed_pixels']:,} ({context['comparison_result']['changed_percentage']:.2f}%)
- Intended Changes: {len(context['comparison_result']['intended_changes'])}
- Unintended Changes: {len(context['comparison_result']['unintended_changes'])}

**Conversation History**:
"""

        for turn in context["turns"]:
            base_prompt += f"\nTurn {turn['turn_number']}:\n"
            base_prompt += f"  Q: {turn['question']}\n"
            base_prompt += f"  A: {turn['answer']}\n"

        base_prompt += f"\n**Current Question (Turn {context['current_turn']}):\n{question}**\n\n"

        if pattern == ConversationPattern.ZOOM:
            base_prompt += "Please zoom in on the specific region mentioned and describe what you see in detail."
        elif pattern == ConversationPattern.ANNOTATE:
            base_prompt += "Please describe what you would annotate or circle to highlight the change."
        elif pattern == ConversationPattern.MEASURE:
            base_prompt += "Please estimate the dimensions or distances mentioned."
        elif pattern == ConversationPattern.COMPARE:
            base_prompt += "Please compare the specific regions mentioned."

        base_prompt += "\n\nProvide a clear, specific answer based on the visual evidence."

        return base_prompt

    def _save_session(self, session: ConversationSession) -> None:
        """Save conversation session to disk.

        Args:
            session: Session to save
        """
        conversations_dir = self.storage_service.config.base_dir / "conversations"
        conversations_dir.mkdir(parents=True, exist_ok=True)

        session_file = conversations_dir / f"{session.session_id}.json"

        try:
            with open(session_file, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            logger.debug(f"Saved conversation session: {session.session_id}")
        except Exception as e:
            logger.error(f"Failed to save conversation session: {e}")

    def load_session(self, session_id: str) -> ConversationSession | None:
        """Load conversation session from disk.

        Args:
            session_id: Session identifier

        Returns:
            Loaded session or None
        """
        conversations_dir = self.storage_service.config.base_dir / "conversations"
        session_file = conversations_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r") as f:
                data = json.load(f)

            # Recreate ComparisonResult
            from wheres_waldo.models.domain import ChangeRegion, Severity

            # Reconstruct turns
            turns = []
            for turn_data in data["turns"]:
                turn = ConversationTurn(
                    turn_number=turn_data["turn_number"],
                    question=turn_data["question"],
                    answer=turn_data["answer"],
                    annotation_path=Path(turn_data["annotation_path"]) if turn_data.get("annotation_path") else None,
                    timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                )
                turns.append(turn)

            # Create session (note: comparison_result will be a placeholder)
            # In practice, you'd load the full comparison result from storage
            session = ConversationSession(
                session_id=data["session_id"],
                comparison_result=None,  # Would need to load from storage
                max_turns=data["max_turns"],
            )
            session.turns = turns
            session.created_at = datetime.fromisoformat(data["created_at"])
            session.is_active = data["is_active"]

            return session

        except Exception as e:
            logger.error(f"Failed to load conversation session: {e}")
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all conversation sessions.

        Returns:
            List of session summaries
        """
        conversations_dir = self.storage_service.config.base_dir / "conversations"

        sessions = []

        for session_file in conversations_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)

                sessions.append({
                    "session_id": data["session_id"],
                    "created_at": data["created_at"],
                    "turns": len(data["turns"]),
                    "max_turns": data["max_turns"],
                    "is_active": data["is_active"],
                })
            except Exception as e:
                logger.error(f"Failed to read session file {session_file}: {e}")

        return sorted(sessions, key=lambda s: s["created_at"], reverse=True)
