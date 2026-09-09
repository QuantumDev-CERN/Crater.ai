"""
Product Brain schema (relational form for the Phase 1 MVP).

Mirrors plan.md §3 (Product Brain) and §33 Phase 1 scope:
    Product / Revision / Component / Connection / Procedure / Failure knowledge

Kept relational (not graph-native) deliberately for the MVP — every
"relationship" table below is a graph edge in disguise, and can be
migrated into a real graph store later (plan.md explicitly defers that:
"later investigate ... knowledge graph").

Revision-awareness is load-bearing: almost every table hangs off
Revision rather than Product, because the plan is explicit that the
agent "must never silently apply information from the wrong revision."
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class DocType(str, enum.Enum):
    manual = "manual"
    schematic = "schematic"
    parts_catalog = "parts_catalog"
    service_ticket = "service_ticket"
    maintenance_schedule = "maintenance_schedule"
    troubleshooting_guide = "troubleshooting_guide"
    other = "other"


class ChunkType(str, enum.Enum):
    text = "text"
    table = "table"
    diagram = "diagram"          # image/schematic region, with OCR'd/captioned text
    procedure_step = "procedure_step"


class RelationType(str, enum.Enum):
    electrical = "electrical"
    mechanical = "mechanical"
    fluid = "fluid"
    signal = "signal"
    contains = "contains"        # part-of / assembly hierarchy


class ProcedureType(str, enum.Enum):
    installation = "installation"
    removal = "removal"
    calibration = "calibration"
    maintenance = "maintenance"
    troubleshooting = "troubleshooting"
    replacement = "replacement"
    verification = "verification"


class IngestionStatus(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Product(Base):
    """A product family, e.g. 'Vulcan OmniPro 220 welder', 'Acme CNC-500'."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    manufacturer: Mapped[str] = mapped_column(String, index=True)
    family: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str] = mapped_column(String, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    revisions: Mapped[list["Revision"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("manufacturer", "family", "model", name="uq_product_identity"),)


class Revision(Base):
    """
    A specific hardware/firmware revision of a Product.

    Every Document, Component, Procedure and FailureMode is scoped to a
    Revision (not just a Product) so the agent can filter/ground answers
    to the correct configuration instead of blending revisions.
    """

    __tablename__ = "revisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    label: Mapped[str] = mapped_column(String)          # e.g. "2023", "Rev C", "fw 4.2"
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="revisions")
    documents: Mapped[list["Document"]] = relationship(back_populates="revision", cascade="all, delete-orphan")
    components: Mapped[list["Component"]] = relationship(back_populates="revision", cascade="all, delete-orphan")
    procedures: Mapped[list["Procedure"]] = relationship(back_populates="revision", cascade="all, delete-orphan")
    failure_modes: Mapped[list["FailureMode"]] = relationship(back_populates="revision", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("product_id", "label", name="uq_revision_label"),)


class Document(Base):
    """A single ingested source file (manual PDF, schematic sheet, etc.)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("revisions.id"), index=True)
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType))
    title: Mapped[str] = mapped_column(String)
    source_path: Mapped[str] = mapped_column(String)   # original filename / storage path
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    revision: Mapped["Revision"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class IngestionJob(Base):
    """Durable status and idempotency record for a document ingestion request."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("revisions.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String)
    content_sha256: Mapped[str] = mapped_column(String)
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType))
    title: Mapped[str] = mapped_column(String)
    source_path: Mapped[str] = mapped_column(String)
    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), default=IngestionStatus.processing)
    stage: Mapped[str] = mapped_column(String, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("revision_id", "idempotency_key", name="uq_ingestion_job_idempotency"),
        UniqueConstraint("revision_id", "content_sha256", name="uq_ingestion_job_content"),
    )


class Chunk(Base):
    """
    An atomic retrievable unit produced by ingestion: a text passage, a
    serialized table, or a diagram region + its OCR/caption text.

    This is what actually gets embedded and pushed into Qdrant / BM25.
    The Qdrant point id == this row's id, so hybrid retrieval can fetch
    full row data (page, doc, revision) after a vector/BM25 hit.
    """

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_type: Mapped[ChunkType] = mapped_column(Enum(ChunkType))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)          # plain text / markdown table / OCR text
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # bbox, image path, table shape, etc.

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Component(Base):
    """A named physical/logical part of the product (relay, sensor, valve...)."""

    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("revisions.id"), index=True)
    name: Mapped[str] = mapped_column(String, index=True)          # e.g. "Relay K17"
    function: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    part_number: Mapped[str | None] = mapped_column(String, nullable=True)
    source_chunk_id: Mapped[str | None] = mapped_column(ForeignKey("chunks.id"), nullable=True)

    revision: Mapped["Revision"] = relationship(back_populates="components")


class ComponentRelationship(Base):
    """A directed edge between two components (the 'Connections' in plan.md §3)."""

    __tablename__ = "component_relationships"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    from_component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    to_component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    relation_type: Mapped[RelationType] = mapped_column(Enum(RelationType))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_chunk_id: Mapped[str | None] = mapped_column(ForeignKey("chunks.id"), nullable=True)


class Procedure(Base):
    """An installation/calibration/troubleshooting/... procedure."""

    __tablename__ = "procedures"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("revisions.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    procedure_type: Mapped[ProcedureType] = mapped_column(Enum(ProcedureType))
    steps: Mapped[list] = mapped_column(JSON)            # ordered list[str]
    source_chunk_id: Mapped[str | None] = mapped_column(ForeignKey("chunks.id"), nullable=True)

    revision: Mapped["Revision"] = relationship(back_populates="procedures")


class FailureMode(Base):
    """
    Symptom -> possible causes -> diagnostic test -> expected observation
    -> repair procedure, per plan.md §3 'Failure knowledge'.

    Phase 1 only needs to *store* this (extracted from docs / seeded
    manually); Phase 2 (Diagnostic Agent) is what walks the graph.
    """

    __tablename__ = "failure_modes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    revision_id: Mapped[str] = mapped_column(ForeignKey("revisions.id"), index=True)
    symptom: Mapped[str] = mapped_column(Text)
    possible_causes: Mapped[list] = mapped_column(JSON)   # list[str]
    diagnostic_test: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    repair_procedure_id: Mapped[str | None] = mapped_column(ForeignKey("procedures.id"), nullable=True)
    source_chunk_id: Mapped[str | None] = mapped_column(ForeignKey("chunks.id"), nullable=True)

    revision: Mapped["Revision"] = relationship(back_populates="failure_modes")
