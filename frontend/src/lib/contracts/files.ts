export interface RawFileSummary {
  file_id: string;
  original_name: string;
  kind: string;
  mode?: string | null;
  created_at: string;
  content_type: string;
  size_bytes: number;
  status: string;
  visibility: string;
  thumbnail_url?: string | null;
  preview_url?: string | null;
  preview_urls?: string[] | null;
  gltf_url?: string | null;
  original_url?: string | null;
  bbox_meta?: Record<string, unknown> | null;
  part_count?: number | null;
  error?: string | null;
}

export interface RawFileDetail extends RawFileSummary {
  lods?: Record<string, { ready?: boolean; url?: string; triangle_count?: number | null }> | null;
  quality_default?: string | null;
  view_mode_default?: string | null;
}

export interface RawFileVersion {
  id: string;
  file_id: string;
  version_number: number;
  created_at: string;
  created_by?: string | null;
  status: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  is_current: boolean;
  metadata?: Record<string, unknown> | null;
}

export interface RawFileStatus {
  state: string;
  derivatives_available: string[];
  progress_hint?: string | null;
  progress_percent?: number | null;
  stage?: string | null;
}

export interface RawAssemblyTreeNode {
  id?: string;
  occurrence_id?: string;
  part_id?: string;
  name?: string;
  display_name?: string;
  kind?: string;
  part_count?: number;
  gltf_nodes?: string[];
  children?: RawAssemblyTreeNode[];
}

export interface RawFileManifest {
  format_version?: string;
  app?: string;
  model_id?: string;
  units?: string;
  bbox?: Record<string, unknown>;
  lod?: Record<string, string>;
  assembly_tree?: RawAssemblyTreeNode[];
  stats?: Record<string, unknown>;
  part_count?: number | null;
}
