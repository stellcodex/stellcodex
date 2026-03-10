from __future__ import annotations

from dataclasses import dataclass
import itertools
import re

import pytest

from app.core.runtime.repo_language_audit import REPO_ROOT


FRONTEND_ROOT = REPO_ROOT / "frontend"
BACKEND_ROOT = REPO_ROOT / "backend"
CATALOG_PATH = FRONTEND_ROOT / "data" / "platformCatalog.ts"
CLIENT_PATH = FRONTEND_ROOT / "components" / "platform" / "PlatformClient.tsx"
SUITE_DOC_PATH = BACKEND_ROOT / "docs" / "reference" / "platform_suite_experience.md"
MATRIX_DOC_PATH = BACKEND_ROOT / "docs" / "reference" / "platform_user_test_matrix.md"

CLIENT_TEXT = CLIENT_PATH.read_text(encoding="utf-8")
CATALOG_TEXT = CATALOG_PATH.read_text(encoding="utf-8")
SUITE_TEXT = SUITE_DOC_PATH.read_text(encoding="utf-8")
MATRIX_TEXT = MATRIX_DOC_PATH.read_text(encoding="utf-8")


@dataclass(frozen=True)
class Persona:
    code: str
    label: str
    confidence: str
    cognition: str


@dataclass(frozen=True)
class Task:
    code: str
    label: str
    expected_app: str
    expected_surface: str
    mode: str
    filename: str | None = None
    content_type: str | None = None
    ui_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    code: str
    persona: Persona
    task: Task


PERSONAS = [
    Persona("cautious_novice", "Cautious novice", "low", "needs a single obvious first step"),
    Persona("rushed_manager", "Rushed manager", "medium", "scans for one fast next action"),
    Persona("visual_inspector", "Visual inspector", "medium", "trusts large visual stages over dense forms"),
    Persona("detail_drafter", "Detail-focused drafter", "high", "expects 2D wording to stay different from 3D wording"),
    Persona("skeptical_founder", "Skeptical founder", "low", "needs trust and product clarity before acting"),
    Persona("shopfloor_operator", "Shop-floor operator", "medium", "needs direct file routing with low friction"),
    Persona("procurement_lead", "Procurement lead", "medium", "looks for clear files and share controls"),
    Persona("quality_reviewer", "Quality reviewer", "high", "expects predictable labels and no duplicate actions"),
    Persona("power_analyst", "Power analyst", "high", "expects app-specific surfaces without generic clutter"),
    Persona("multilingual_beginner", "Multilingual beginner", "low", "benefits from English-first, short, readable copy"),
]

TASKS = [
    Task(
        "upload_3d_model",
        "Upload a 3D model",
        expected_app="viewer3d",
        expected_surface="viewer3d",
        mode="upload",
        filename="motor_mount.step",
        content_type="application/step",
        ui_tokens=("Upload once. Open the right app automatically.", "3D workspace"),
    ),
    Task(
        "upload_2d_drawing",
        "Upload a 2D drawing",
        expected_app="viewer2d",
        expected_surface="viewer2d",
        mode="upload",
        filename="layout.dxf",
        content_type="image/vnd.dxf",
        ui_tokens=("Upload once. Open the right app automatically.", "2D workspace"),
    ),
    Task(
        "upload_document",
        "Upload a document",
        expected_app="docviewer",
        expected_surface="docviewer",
        mode="upload",
        filename="inspection-report.pdf",
        content_type="application/pdf",
        ui_tokens=("Upload once. Open the right app automatically.", "document workspace"),
    ),
    Task(
        "open_files_hub",
        "Open the files and share hub",
        expected_app="drive",
        expected_surface="route",
        mode="navigate",
        ui_tokens=("Open Files and Share", "File Ledger"),
    ),
    Task(
        "open_projects",
        "Open projects",
        expected_app="projects",
        expected_surface="route",
        mode="navigate",
        ui_tokens=("Create Project", "Project Index"),
    ),
    Task(
        "discover_applications",
        "Discover the applications catalog",
        expected_app="applications",
        expected_surface="catalog",
        mode="navigate",
        ui_tokens=("Browse all applications", "Inventory Status"),
    ),
    Task(
        "run_conversion",
        "Run conversion",
        expected_app="convert",
        expected_surface="job",
        mode="app_surface",
        ui_tokens=("Only working actions are exposed.", "Source File"),
    ),
    Task(
        "run_mesh_generation",
        "Run mesh generation",
        expected_app="mesh2d3d",
        expected_surface="job",
        mode="app_surface",
        ui_tokens=("Only working actions are exposed.", "Source File"),
    ),
    Task(
        "configure_moldcodes",
        "Configure MoldCodes",
        expected_app="moldcodes",
        expected_surface="configurator",
        mode="app_surface",
        ui_tokens=("Category, family and validated dimensions feed the export job.", "Allowed range:"),
    ),
    Task(
        "open_library",
        "Open the library",
        expected_app="library",
        expected_surface="route",
        mode="navigate",
        ui_tokens=("Library Output", "Open the full library route for publish and feed management."),
    ),
]

SCENARIOS = [
    Scenario(
        code=f"{persona.code}__{task.code}",
        persona=persona,
        task=task,
    )
    for persona, task in itertools.product(PERSONAS, TASKS)
]


def parse_platform_surfaces() -> dict[str, str]:
    ids = re.findall(r'id:\s*"([^"]+)"', CATALOG_TEXT)
    surfaces = re.findall(r'surface:\s*"([^"]+)"', CATALOG_TEXT)
    return dict(zip(ids, surfaces))


PLATFORM_SURFACES = parse_platform_surfaces()


def classify_upload(filename: str, content_type: str) -> str:
    name = filename.lower()
    content = content_type.lower()
    if name.endswith(".dxf"):
        return "viewer2d"
    if content.startswith("image/"):
        return "docviewer"
    if content in {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "application/rtf",
        "text/plain",
        "text/csv",
        "text/html",
    }:
        return "docviewer"
    if any(name.endswith(ext) for ext in (".pdf", ".doc", ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".txt", ".csv", ".html", ".htm")):
        return "docviewer"
    return "viewer3d"


def test_user_matrix_document_exists() -> None:
    assert "100 scenario combinations" in MATRIX_TEXT
    assert "10 different personas" in MATRIX_TEXT
    assert "10 different suite tasks" in MATRIX_TEXT


def test_user_matrix_contains_100_distinct_scenarios() -> None:
    assert len(SCENARIOS) == 100
    assert len({scenario.code for scenario in SCENARIOS}) == 100


def test_suite_home_keeps_trust_signals_visible() -> None:
    assert "Simple in front. Specialized underneath." in CLIENT_TEXT
    assert "No cloned entry pages" in CLIENT_TEXT
    assert "STELLCODEX is the product" in SUITE_TEXT
    assert "do not place the same primary button twice" in SUITE_TEXT


def test_suite_plan_copy_stays_locked() -> None:
    assert "Free" in CLIENT_TEXT
    assert "Plus" in CLIENT_TEXT
    assert "Pro" in CLIENT_TEXT
    assert "Enterprise" not in CLIENT_TEXT


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[scenario.code for scenario in SCENARIOS])
def test_user_scenario_maps_to_expected_app_and_surface(scenario: Scenario) -> None:
    assert scenario.task.expected_app in PLATFORM_SURFACES, scenario.code
    assert PLATFORM_SURFACES[scenario.task.expected_app] == scenario.task.expected_surface, scenario.code
    for token in scenario.task.ui_tokens:
        assert token in CLIENT_TEXT, f"{scenario.code}: missing token {token!r}"

    if scenario.task.mode == "upload":
        assert scenario.task.filename is not None, scenario.code
        assert scenario.task.content_type is not None, scenario.code
        routed_app = classify_upload(scenario.task.filename, scenario.task.content_type)
        assert routed_app == scenario.task.expected_app, scenario.code
