"use client";

import { useMemo, useState } from "react";
import type { RequiredInputField } from "@/lib/contracts/orchestrator";

export function useRequiredInputs(initialFields: RequiredInputField[]) {
  const [fields, setFields] = useState<RequiredInputField[]>(initialFields);

  const errors = useMemo(
    () =>
      fields.reduce<Record<string, string>>((acc, field) => {
        const value = field.value;
        const empty = value == null || value === "" || (Array.isArray(value) && value.length === 0);
        if (field.required && empty) {
          acc[field.key] = "This input is required.";
        }
        return acc;
      }, {}),
    [fields]
  );

  function updateField(key: string, value: RequiredInputField["value"]) {
    setFields((current) => current.map((field) => (field.key === key ? { ...field, value, error: null } : field)));
  }

  function validate() {
    setFields((current) =>
      current.map((field) => ({
        ...field,
        error: errors[field.key] || null,
      }))
    );
    return Object.keys(errors).length === 0;
  }

  return { fields, setFields, updateField, validate, errors };
}
