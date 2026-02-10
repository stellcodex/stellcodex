"use client";

import { useEffect, useState } from "react";
import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/Button";

type ProviderMap = Record<string, { id: string; name: string }>;

export function LoginButton() {
  const [providers, setProviders] = useState<ProviderMap | null>(null);

  useEffect(() => {
    fetch("/api/auth/providers")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setProviders(data))
      .catch(() => setProviders(null));
  }, []);

  const providerList = providers ? Object.values(providers) : [];
  const primary = providerList[0];

  if (!primary) {
    return (
      <Button variant="secondary" disabled>
        Giriş yakında. Şimdilik misafir modunda dosya yükleyebilirsin.
      </Button>
    );
  }

  return <Button onClick={() => signIn(primary.id)}>{primary.name} ile Giriş</Button>;
}
