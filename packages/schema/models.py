from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SectionKind(str, Enum):
    ABSTRACT = "abstract"
    KEYWORDS = "keywords"
    INTRO = "intro"
    METHOD = "method"
    EXPERIMENT = "experiment"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    ENGLISH = "english"
    OTHER = "other"


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    FORMULA = "formula"
    FIGURE_REF = "figure_ref"
    LIST = "list"


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckCategory(str, Enum):
    STRUCTURE = "structure"
    FORMAT = "format"
    CONSISTENCY = "consistency"
    REFERENCE = "reference"


class JobStatus(str, Enum):
    QUEUED = "queued"
    CONVERTING = "converting"
    PARSING = "parsing"
    CHECKING = "checking"
    DONE = "done"
    FAILED = "failed"


class PaperMeta(BaseModel):
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    doi: str | None = None
    keywords: list[str] = Field(default_factory=list)
    abstract: str = ""
    english_abstract: str = ""
    english_title: str = ""
    classification: str | None = None


class Section(BaseModel):
    id: str
    kind: SectionKind
    title: str
    level: int = 1
    start_line: int
    end_line: int
    parent_id: str | None = None


class Block(BaseModel):
    id: str
    type: BlockType
    section_id: str
    line_start: int
    line_end: int
    text: str = ""
    raw: str = ""


class TableData(BaseModel):
    id: str
    caption: str = ""
    number: int | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    source: str = "maker"
    html: str | None = None


class FigureRef(BaseModel):
    id: str
    number: int | None = None
    caption: str = ""
    path: str | None = None
    line: int | None = None


class Reference(BaseModel):
    index: int
    raw_text: str
    authors: str | None = None
    title: str | None = None
    journal: str | None = None
    year: str | None = None


class Citation(BaseModel):
    ref_indices: list[int] = Field(default_factory=list)
    section_id: str
    line: int
    context: str = ""


class ParseQuality(BaseModel):
    maker_score: float = 1.0
    mineru_score: float = 1.0
    fusion_score: float = 1.0
    fusion_warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class PaperDocument(BaseModel):
    meta: PaperMeta = Field(default_factory=PaperMeta)
    sections: list[Section] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    figures: list[FigureRef] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    quality: ParseQuality = Field(default_factory=ParseQuality)
    source_files: dict[str, str] = Field(default_factory=dict)


class Issue(BaseModel):
    code: str
    category: CheckCategory
    severity: IssueSeverity
    section: str | None = None
    line: int | None = None
    message: str
    suggestion: str = ""
    evidence: str = ""


class ReportSummary(BaseModel):
    errors: int = 0
    warnings: int = 0
    infos: int = 0


class CheckReport(BaseModel):
    job_id: str
    parse_quality: ParseQuality
    summary: ReportSummary
    issues: list[Issue] = Field(default_factory=list)
    checks_run: list[CheckCategory] = Field(default_factory=list)
    paper_title: str = ""


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    journal_profile: str = "generic"
    user_id: str | None = None
    filename: str | None = None
    error: str | None = None
    report: CheckReport | None = None
    created_at: str = ""
    updated_at: str = ""


class JobListItem(BaseModel):
    job_id: str
    status: JobStatus
    journal_profile: str
    filename: str | None = None
    paper_title: str | None = None
    summary: ReportSummary | None = None
    created_at: str = ""
    updated_at: str = ""


class ConsistencyLLMResult(BaseModel):
    coverage_gaps: list[str] = Field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = Field(default_factory=list)


class UserPublic(BaseModel):
    id: str
    email: str
    name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str
