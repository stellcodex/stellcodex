"use client";

import { ErrorState } from "@/components/ui/StateBlocks";
import { Button } from "@/components/ui/Button";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <ErrorState
        title="Something went wrong"
        description={error?.message || "Unexpected error."}
        action={
          <Button variant="secondary" onClick={reset}>
            Retry
          </Button>
        }
      />
    </div>
  );
}
