"use client";

import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { AppPage } from "@/components/shell/AppPage";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { Button } from "@/components/primitives/Button";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { ShareTable } from "@/components/shares/ShareTable";
import { useShares } from "@/lib/hooks/useShares";

export default function SharesPage() {
  const { data, loading, error, refresh, create, revoke } = useShares();
  const [open, setOpen] = useState(false);

  return (
    <AppShell title="Shares" subtitle="Create, open, and revoke secure shares" breadcrumbs={[{ label: "Shares" }]}>
      <AppPage
        title="Shares"
        subtitle="Only real share operations are exposed"
        actions={
          <Button variant="primary" onClick={() => setOpen(true)}>
            Create share
          </Button>
        }
      >
        {loading ? <LoadingSkeleton label="Loading shares" /> : null}
        {error ? <ErrorState title="Shares unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
        {!loading && !error ? <ShareTable shares={data} onRevoke={(shareId) => void revoke(shareId)} /> : null}
        <ShareDialog
          open={open}
          onClose={() => setOpen(false)}
          onSubmit={async (value) => {
            await create(value.fileId, value.permission, value.expiresInSeconds);
            setOpen(false);
          }}
        />
      </AppPage>
    </AppShell>
  );
}
