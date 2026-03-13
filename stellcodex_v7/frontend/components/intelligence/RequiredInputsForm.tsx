"use client";

import type { RequiredInputField } from "@/lib/contracts/orchestrator";
import { Button } from "@/components/primitives/Button";
import { Checkbox } from "@/components/primitives/Checkbox";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";
import { Textarea } from "@/components/primitives/Textarea";

export interface RequiredInputsFormProps {
  fields: RequiredInputField[];
  onChange: (key: string, value: RequiredInputField["value"]) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function RequiredInputsForm({ fields, onChange, onSubmit, disabled = false }: RequiredInputsFormProps) {
  return (
    <div className="sc-stack">
      {fields.map((field) => (
        <label key={field.key} className="sc-stack">
          <span>{field.label}</span>
          {field.type === "textarea" ? (
            <Textarea value={String(field.value || "")} error={field.error} onChange={(event) => onChange(field.key, event.target.value)} />
          ) : field.type === "select" ? (
            <Select value={String(field.value || "")} error={field.error} onChange={(event) => onChange(field.key, event.target.value)}>
              <option value="">Select</option>
              {(field.options || []).map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          ) : field.type === "boolean" ? (
            <Checkbox checked={Boolean(field.value)} label={field.helpText || field.label} onChange={(event) => onChange(field.key, event.target.checked)} />
          ) : (
            <Input
              type={field.type === "number" ? "number" : "text"}
              value={field.value == null ? "" : String(field.value)}
              error={field.error}
              onChange={(event) => onChange(field.key, field.type === "number" ? Number(event.target.value) : event.target.value)}
            />
          )}
          {field.helpText ? <span className="sc-muted">{field.helpText}</span> : null}
          {field.error ? <span className="sc-muted">{field.error}</span> : null}
        </label>
      ))}
      <Button variant="primary" onClick={onSubmit} disabled={disabled}>
        Submit inputs
      </Button>
    </div>
  );
}
