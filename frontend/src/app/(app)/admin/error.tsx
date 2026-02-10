"use client";

import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/StateBlocks";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <ErrorState
      title="Admin error"
      description={error?.message || "Unexpected error."}
      action={
        <Button variant="secondary" onClick={reset}>
          Retry
        </Button>
      }
    />
  );
}
