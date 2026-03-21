"use client";

import * as React from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { resolvePublicShare } from "@/lib/api/shares";
import { ApiError } from "@/lib/api/fetch";
import { mapPublicShareRecord, mapPublicShareTerminalState } from "@/lib/mappers/shareMappers";

import { PublicShareTerminalState } from "./PublicShareTerminalState";

export interface PublicShareScreenProps {
  token: string;
}

function ModelPreview({ url }: { url: string }) {
  function PublicModelScene({ modelUrl }: { modelUrl: string }) {
    const gltf = useLoader(GLTFLoader, modelUrl);
    const scene = React.useMemo(() => gltf.scene.clone(true), [gltf.scene]);

    return (
      <>
        <ambientLight intensity={0.9} />
        <directionalLight intensity={1.1} position={[6, 8, 6]} />
        <primitive object={scene} />
        <OrbitControls />
      </>
    );
  }

  return (
    <div className="h-[72vh] overflow-hidden rounded-[12px] border border-[#eeeeee] bg-white">
      <Canvas camera={{ position: [8, 8, 8], fov: 45 }}>
        <React.Suspense fallback={null}>
          <PublicModelScene modelUrl={url} />
        </React.Suspense>
      </Canvas>
    </div>
  );
}

export function PublicShareScreen({ token }: PublicShareScreenProps) {
  const [share, setShare] = React.useState<ReturnType<typeof mapPublicShareRecord> | null>(null);
  const [state, setState] = React.useState<"loading" | "valid" | "expired" | "revoked" | "invalid">("loading");

  React.useEffect(() => {
    void resolvePublicShare(token)
      .then((response) => {
        setShare(mapPublicShareRecord(response));
        setState("valid");
      })
      .catch((caughtError) => {
        if (caughtError instanceof ApiError) {
          setState(mapPublicShareTerminalState(caughtError.status));
          return;
        }
        setState("invalid");
      });
  }, [token]);

  if (state === "loading") return <RouteLoadingState title="Resolving public share" />;
  if (state === "expired") return <PublicShareTerminalState description="This share token has expired and now returns a terminal state." title="Link expired" />;
  if (state === "revoked") return <PublicShareTerminalState description="This share token has been revoked or access has been removed." title="Share revoked" />;
  if (state === "invalid" || !share) return <PublicShareTerminalState description="The share token is invalid or forbidden." title="Share unavailable" />;
  if (!share.gltfUrl && !share.originalUrl) {
    return <PublicShareTerminalState description="No public viewer content is available for this token." title="Preview unavailable" />;
  }

  return (
    <main className="min-h-screen bg-white px-4 py-8">
      <div className="mx-auto max-w-[1200px] space-y-6">
        <h1 className="text-[18px] font-semibold text-[var(--foreground-strong)]">{share.originalFilename}</h1>
        {share.gltfUrl ? <ModelPreview url={share.gltfUrl} /> : null}
        {!share.gltfUrl && share.originalUrl ? (
          <div className="h-[72vh] overflow-hidden rounded-[12px] border border-[#eeeeee] bg-white">
            <iframe className="h-full w-full border-0" src={share.originalUrl} title={share.originalFilename} />
          </div>
        ) : null}
      </div>
    </main>
  );
}
