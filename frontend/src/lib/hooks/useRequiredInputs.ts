"use client";

import * as React from "react";

import { getRequiredInputs } from "@/lib/api/orchestrator";
import { mapRequiredInputRecords } from "@/lib/mappers/orchestratorMappers";

export function useRequiredInputs(sessionId: string | null) {
  const [fields, setFields] = React.useState<ReturnType<typeof mapRequiredInputRecords>>([]);
  const [values, setValues] = React.useState<Record<string, string>>({});
  const [loading, setLoading] = React.useState(Boolean(sessionId));
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    if (!sessionId) {
      setFields([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await getRequiredInputs(sessionId);
      const mapped = mapRequiredInputRecords(response);
      setFields(mapped);
      setValues((current) =>
        mapped.reduce<Record<string, string>>((result, field) => {
          result[field.key] = current[field.key] ?? "";
          return result;
        }, {}),
      );
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Required inputs could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  function setValue(key: string, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function validate() {
    return fields.filter((field) => field.required && !values[field.key]?.trim()).map((field) => field.label);
  }

  async function submit() {
    const missing = validate();
    if (missing.length > 0) {
      setError(`Required inputs missing: ${missing.join(", ")}.`);
      return false;
    }
    setError("Input submission is not exposed by the current backend contract.");
    return false;
  }

  return { fields, values, loading, error, setValue, validate, submit, refresh };
}
