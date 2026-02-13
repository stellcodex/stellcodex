import { Suspense } from "react";
import App2DClient from "./App2DClient";

export default function App2DPage() {
  return (
    <Suspense fallback={<div className="p-5 text-sm text-slate-500">Yükleniyor...</div>}>
      <App2DClient />
    </Suspense>
  );
}
