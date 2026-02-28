CREATE TABLE IF NOT EXISTS library_items (
  id UUID PRIMARY KEY,
  owner_key TEXT NOT NULL,
  owner_user_id UUID NULL,
  file_id TEXT NOT NULL,
  visibility VARCHAR(16) NOT NULL DEFAULT 'private',
  slug VARCHAR(180) NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  cover_thumb TEXT NULL,
  share_token VARCHAR(128) NULL,
  stats JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_library_items_owner_key ON library_items(owner_key);
CREATE INDEX IF NOT EXISTS ix_library_items_owner_user_id ON library_items(owner_user_id);
CREATE INDEX IF NOT EXISTS ix_library_items_file_id ON library_items(file_id);
CREATE INDEX IF NOT EXISTS ix_library_items_slug ON library_items(slug);
CREATE INDEX IF NOT EXISTS ix_library_items_visibility ON library_items(visibility);

