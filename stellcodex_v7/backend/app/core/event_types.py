from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    FILE_UPLOADED = "file.uploaded"
    FILE_CONVERT_STARTED = "file.convert.started"
    FILE_CONVERTED = "file.converted"
    ASSEMBLY_READY = "assembly.ready"
    DECISION_READY = "decision.ready"
    DFM_READY = "dfm.ready"
    REPORT_READY = "report.ready"
    PACKAGE_READY = "package.ready"
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    JOB_FAILED = "job.failed"


class StageName(str, Enum):
    CONVERT = "convert"
    ASSEMBLY_META = "assembly_meta"
    RULE_ENGINE = "rule_engine"
    DFM = "dfm"
    REPORT = "report"
    PACK = "pack"


STAGE_SEQUENCE: tuple[StageName, ...] = (
    StageName.CONVERT,
    StageName.ASSEMBLY_META,
    StageName.RULE_ENGINE,
    StageName.DFM,
    StageName.REPORT,
    StageName.PACK,
)


EVENT_STAGE_MAP: dict[str, StageName] = {
    EventType.FILE_UPLOADED.value: StageName.CONVERT,
    EventType.FILE_CONVERTED.value: StageName.ASSEMBLY_META,
    EventType.ASSEMBLY_READY.value: StageName.RULE_ENGINE,
    EventType.DECISION_READY.value: StageName.DFM,
    EventType.DFM_READY.value: StageName.REPORT,
    EventType.REPORT_READY.value: StageName.PACK,
}


NEXT_EVENT_BY_STAGE: dict[StageName, EventType] = {
    StageName.CONVERT: EventType.FILE_CONVERTED,
    StageName.ASSEMBLY_META: EventType.ASSEMBLY_READY,
    StageName.RULE_ENGINE: EventType.DECISION_READY,
    StageName.DFM: EventType.DFM_READY,
    StageName.REPORT: EventType.REPORT_READY,
    StageName.PACK: EventType.PACKAGE_READY,
}


FAILURE_CODES: tuple[str, ...] = (
    "CONVERT_FAIL",
    "ASSEMBLY_META_FAIL",
    "DECISION_FAIL",
    "DFM_FAIL",
    "REPORT_FAIL",
    "PACKAGE_FAIL",
    "STORAGE_FAIL",
    "UNKNOWN",
)
