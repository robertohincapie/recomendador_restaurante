from enum import Enum
from math import sqrt
from typing import List
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    open = "open"
    single = "single"
    multiple = "multiple"


class QuestionDesignRequest(BaseModel):
    objective: str = Field(min_length=5, max_length=300)
    context: str = Field(default="", max_length=600)
    expected_answers: int = Field(ge=1, le=10000)
    candidate_options: List[str] = Field(default_factory=list)


class QuestionBlueprint(BaseModel):
    question: str
    question_type: QuestionType
    min_answers: int
    max_answers: int
    options: List[str] = Field(default_factory=list)


class QuestionTopologyPolicy:
    def define_type(self, expected_answers: int, candidate_options: List[str]) -> QuestionType:
        if expected_answers <= 3:
            return QuestionType.open
        if expected_answers <= 15 and len(candidate_options) <= 3:
            return QuestionType.single
        return QuestionType.multiple


class OptionSizer:
    def define_option_count(self, expected_answers: int) -> int:
        raw = int(round(sqrt(expected_answers) + 1))
        return max(2, min(8, raw))

    def define_max_answers(self, option_count: int) -> int:
        raw = int(round(option_count * 0.4))
        return max(1, min(5, raw))


class QuestionTextBuilder:
    def build(self, objective: str, context: str) -> str:
        objective_text = objective.strip().rstrip("?")
        if context.strip():
            return f"{objective_text} ({context.strip()})?"
        return f"{objective_text}?"


class OptionBuilder:
    def build(self, candidate_options: List[str], option_count: int) -> List[str]:
        cleaned = []
        for option in candidate_options:
            value = option.strip()
            if value and value not in cleaned:
                cleaned.append(value)
        if len(cleaned) >= option_count:
            return cleaned[:option_count]
        generic = [
            "Muy bajo",
            "Bajo",
            "Medio",
            "Alto",
            "Muy alto",
            "No aplica",
            "Depende",
            "Prefiero no responder",
        ]
        for option in generic:
            if len(cleaned) >= option_count:
                break
            if option not in cleaned:
                cleaned.append(option)
        return cleaned


class QuestionDesigner:
    def __init__(self) -> None:
        self._policy = QuestionTopologyPolicy()
        self._sizer = OptionSizer()
        self._text_builder = QuestionTextBuilder()
        self._option_builder = OptionBuilder()

    def design(self, request: QuestionDesignRequest) -> QuestionBlueprint:
        question_type = self._policy.define_type(request.expected_answers, request.candidate_options)
        question_text = self._text_builder.build(request.objective, request.context)
        if question_type == QuestionType.open:
            return QuestionBlueprint(
                question=question_text,
                question_type=question_type,
                min_answers=1,
                max_answers=1,
                options=[],
            )
        option_count = self._sizer.define_option_count(request.expected_answers)
        options = self._option_builder.build(request.candidate_options, option_count)
        if question_type == QuestionType.single:
            return QuestionBlueprint(
                question=question_text,
                question_type=question_type,
                min_answers=1,
                max_answers=1,
                options=options,
            )
        max_answers = min(len(options), self._sizer.define_max_answers(len(options)))
        return QuestionBlueprint(
            question=question_text,
            question_type=question_type,
            min_answers=1,
            max_answers=max_answers,
            options=options,
        )
