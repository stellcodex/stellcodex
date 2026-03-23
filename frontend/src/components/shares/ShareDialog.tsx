"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { Dialog } from "@/components/primitives/Dialog";
import { RadioGroup } from "@/components/primitives/RadioGroup";
import { Select } from "@/components/primitives/Select";

export interface ShareDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (permission: string, expiresInSeconds: number) => Promise<void>;
}

const expiryOptions = [
  { label: "1 day", value: 24 * 60 * 60 },
  { label: "7 days", value: 7 * 24 * 60 * 60 },
  { label: "30 days", value: 30 * 24 * 60 * 60 },
];

export function ShareDialog({ onClose, onCreate, open }: ShareDialogProps) {
  const [permission, setPermission] = React.useState("view");
  const [expires, setExpires] = React.useState(String(expiryOptions[1].value));
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      await onCreate(permission, Number(expires));
      onClose();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The share could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onClose={onClose} open={open} title="Create Share">
      <div className="space-y-5">
        <RadioGroup
          name="share-permission"
          onChange={setPermission}
          options={[
            { label: "View", value: "view", description: "Allow public viewing only." },
            { label: "Comment", value: "comment", description: "Create the share with comment permission." },
            { label: "Download", value: "download", description: "Allow download when the share contract permits it." },
          ]}
          value={permission}
        />
        <div className="space-y-2">
          <label className="text-sm font-medium">Expiry</label>
          <Select onChange={(event) => setExpires(event.target.value)} value={expires}>
            {expiryOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
        {error ? <div className="text-sm text-[var(--status-danger-fg)]">{error}</div> : null}
        <div className="flex justify-end gap-3">
          <Button onClick={onClose} variant="secondary">Cancel</Button>
          <Button onClick={() => void handleSubmit()} variant="primary">
            {submitting ? "Creating..." : "Create share"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
