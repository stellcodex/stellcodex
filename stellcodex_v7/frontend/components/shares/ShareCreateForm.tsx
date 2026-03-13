"use client";

import { useState } from "react";
import { Button } from "@/components/primitives/Button";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";

export interface ShareCreateFormProps {
  onSubmit: (value: { fileId: string; permission: "view" | "comment" | "download"; expiresInSeconds: number }) => void;
  defaultFileId?: string;
}

export function ShareCreateForm({ onSubmit, defaultFileId = "" }: ShareCreateFormProps) {
  const [fileId, setFileId] = useState(defaultFileId);
  const [permission, setPermission] = useState<"view" | "comment" | "download">("view");
  const [days, setDays] = useState("7");

  const expiresInSeconds = Number(days) * 24 * 60 * 60;
  const invalid = !fileId || !Number.isFinite(expiresInSeconds) || expiresInSeconds <= 0;

  return (
    <div className="sc-stack">
      <Input value={fileId} placeholder="file_id" onChange={(event) => setFileId(event.target.value)} />
      <Select value={permission} onChange={(event) => setPermission(event.target.value as "view" | "comment" | "download")}>
        <option value="view">View</option>
        <option value="comment">Comment</option>
        <option value="download">Download</option>
      </Select>
      <Input type="number" min="1" value={days} onChange={(event) => setDays(event.target.value)} />
      <Button variant="primary" disabled={invalid} onClick={() => onSubmit({ fileId, permission, expiresInSeconds })}>
        Create share
      </Button>
    </div>
  );
}
