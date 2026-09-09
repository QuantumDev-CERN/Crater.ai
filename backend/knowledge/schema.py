"""Pydantic shapes for LLM-structured extraction output (knowledge/component_extraction.py)."""
from __future__ import annotations

from pydantic import BaseModel


class ExtractedComponent(BaseModel):
    name: str
    function: str | None = None
    location_description: str | None = None
    part_number: str | None = None


class ExtractedRelationship(BaseModel):
    from_component: str
    to_component: str
    relation_type: str  # electrical | mechanical | fluid | signal | contains
    description: str | None = None


class ExtractedProcedure(BaseModel):
    name: str
    procedure_type: str  # installation | removal | calibration | maintenance | troubleshooting | replacement | verification
    steps: list[str]


class ExtractionResult(BaseModel):
    components: list[ExtractedComponent] = []
    relationships: list[ExtractedRelationship] = []
    procedures: list[ExtractedProcedure] = []
