import { Suspense } from "react";
import AppRenderClient from "./AppRenderClient";

export default function RenderPage() {
  return (
    <Suspense fallback={<div className="p-5 text-sm text-slate-500">Yükleniyor...</div>}>
      <AppRenderClient />
    </Suspense>
  );
}
