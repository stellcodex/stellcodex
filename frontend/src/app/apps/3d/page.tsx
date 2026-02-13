import { Suspense } from "react";
import App3DClient from "./App3DClient";

export default function App3DPage() {
  return (
    <Suspense fallback={<div className="p-5 text-sm text-slate-500">Yükleniyor...</div>}>
      <App3DClient />
    </Suspense>
  );
}
