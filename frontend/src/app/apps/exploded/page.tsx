import { Suspense } from "react";
import AppExplodedClient from "./AppExplodedClient";

export default function ExplodedPage() {
  return (
    <Suspense fallback={<div className="p-5 text-sm text-slate-500">Yükleniyor...</div>}>
      <AppExplodedClient />
    </Suspense>
  );
}
