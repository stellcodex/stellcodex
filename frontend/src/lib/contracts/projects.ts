export interface RawProjectFile {
  file_id: string;
  original_filename: string;
  status: string;
  kind?: string | null;
  mode?: string | null;
  created_at?: string | null;
}

export interface RawProject {
  id: string;
  name: string;
  file_count: number;
  updated_at?: string | null;
  files: RawProjectFile[];
}
