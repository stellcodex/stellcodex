-- V7 explorer support: folder_key for uploaded_files
ALTER TABLE uploaded_files
ADD COLUMN IF NOT EXISTS folder_key TEXT;

CREATE INDEX IF NOT EXISTS ix_uploaded_files_folder_key
ON uploaded_files (folder_key);
