export interface RawShare {
  id: string;
  token: string;
  expires_at: string;
  permission: string;
}

export interface RawShareList {
  items: RawShare[];
}

export interface RawPublicShare {
  file_id: string;
  status: string;
  permission: string;
  can_view: boolean;
  can_download: boolean;
  expires_at: string;
  content_type: string;
  original_filename: string;
  size_bytes: number;
  gltf_url?: string | null;
  original_url?: string | null;
  expires_in_seconds?: number;
}
