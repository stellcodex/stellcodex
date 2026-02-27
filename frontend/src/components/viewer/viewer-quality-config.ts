import type { RenderMode } from "@/components/viewer/ThreeViewer";

export type QualityLevel = "Ultra" | "High" | "Medium" | "Low";
export type ViewerModeKey = RenderMode;
export type LodLevel = "lod0" | "lod1" | "lod2";

export const VIEWER_MODE_ORDER: ViewerModeKey[] = ["shadedEdges", "shaded", "xray", "wireframe", "pbr"];

export const VIEWER_MODE_LABEL: Record<ViewerModeKey, string> = {
  shaded: "Shaded",
  shadedEdges: "Shaded + Edges",
  xray: "Hidden Line / X-Ray",
  wireframe: "Wireframe",
  pbr: "PBR View",
};

export const QUALITY_TO_LOD: Record<QualityLevel, LodLevel> = {
  Ultra: "lod2",
  High: "lod1",
  Medium: "lod1",
  Low: "lod0",
};

export const QUALITY_DEFAULT: QualityLevel = "Medium";

export const CAMERA_PRESETS = [
  { key: "iso", label: "Iso", pos: [2, 2, 2] as const },
  { key: "front", label: "Front", pos: [0, 0, 3] as const },
  { key: "top", label: "Top", pos: [0, 3, 0] as const },
  { key: "right", label: "Right", pos: [3, 0, 0] as const },
] as const;
