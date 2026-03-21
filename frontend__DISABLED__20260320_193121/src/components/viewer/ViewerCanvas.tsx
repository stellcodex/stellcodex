"use client";

import * as React from "react";
import { Canvas, useLoader, useThree } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { Box3, Color, Mesh, MeshStandardMaterial, Object3D, Vector3 } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

import { ErrorState } from "@/components/primitives/ErrorState";
import { EmptyState } from "@/components/primitives/EmptyState";
import type { ViewerModel, ViewerNodeRecord } from "@/lib/contracts/ui";

function flattenNodes(nodes: ViewerNodeRecord[]) {
  const result: ViewerNodeRecord[] = [];
  const visit = (entries: ViewerNodeRecord[]) => {
    for (const entry of entries) {
      result.push(entry);
      visit(entry.children);
    }
  };
  visit(nodes);
  return result;
}

function buildNodeNameIndex(nodes: ViewerNodeRecord[]) {
  const map = new Map<string, string>();
  for (const node of flattenNodes(nodes)) {
    for (const nodeName of node.gltfNodes) {
      map.set(nodeName, node.occurrenceId);
    }
  }
  return map;
}

function collectNodeNames(nodes: ViewerNodeRecord[], targetIds: string[]) {
  const targetSet = new Set(targetIds);
  const names = new Set<string>();
  for (const node of flattenNodes(nodes)) {
    if (!targetSet.has(node.occurrenceId)) continue;
    node.gltfNodes.forEach((name) => names.add(name));
  }
  return names;
}

interface OrbitControlsHandle {
  target: Vector3;
  update: () => void;
}

function fitCameraToObjects(cameraObject: Object3D, controls: OrbitControlsHandle | null, root: Object3D, targetNames?: Set<string>) {
  const bounds = new Box3();
  root.traverse((object) => {
    if (targetNames && targetNames.size > 0 && !targetNames.has(object.name)) return;
    if (!object.visible) return;
    bounds.expandByObject(object);
  });
  if (bounds.isEmpty()) return;
  const size = new Vector3();
  const center = new Vector3();
  bounds.getSize(size);
  bounds.getCenter(center);
  const maxDimension = Math.max(size.x, size.y, size.z) || 1;
  cameraObject.position.set(center.x + maxDimension * 1.4, center.y + maxDimension * 1.4, center.z + maxDimension * 1.4);
  if ("near" in cameraObject) {
    const camera = cameraObject as Object3D & {
      near: number;
      far: number;
      updateProjectionMatrix: () => void;
    };
    camera.near = maxDimension / 100;
    camera.far = maxDimension * 100;
    camera.updateProjectionMatrix();
  }
  controls?.target.copy(center);
  controls?.update();
}

function ModelScene({
  nodes,
  onSelectOccurrence,
  selectedOccurrenceIds,
  hiddenOccurrenceIds,
  isolatedOccurrenceId,
  modelUrl,
  fitSequence,
  fitMode,
}: {
  nodes: ViewerNodeRecord[];
  onSelectOccurrence: (occurrenceId: string) => void;
  selectedOccurrenceIds: string[];
  hiddenOccurrenceIds: string[];
  isolatedOccurrenceId: string | null;
  modelUrl: string;
  fitSequence: number;
  fitMode: "model" | "selection" | "reset" | null;
}) {
  const gltf = useLoader(GLTFLoader, modelUrl);
  const scene = React.useMemo(() => gltf.scene.clone(true), [gltf.scene]);
  const controlsRef = React.useRef<OrbitControlsImpl | null>(null);
  const { camera } = useThree();

  const nodeNameToOccurrence = React.useMemo(() => buildNodeNameIndex(nodes), [nodes]);
  const selectedNodeNames = React.useMemo(() => collectNodeNames(nodes, selectedOccurrenceIds), [nodes, selectedOccurrenceIds]);
  const hiddenNodeNames = React.useMemo(() => collectNodeNames(nodes, hiddenOccurrenceIds), [hiddenOccurrenceIds, nodes]);
  const isolatedNodeNames = React.useMemo(
    () => (isolatedOccurrenceId ? collectNodeNames(nodes, [isolatedOccurrenceId]) : null),
    [isolatedOccurrenceId, nodes],
  );

  React.useEffect(() => {
    scene.traverse((object) => {
      if (hiddenNodeNames.has(object.name)) {
        object.visible = false;
        return;
      }
      if (isolatedNodeNames && isolatedNodeNames.size > 0 && nodeNameToOccurrence.has(object.name) && !isolatedNodeNames.has(object.name)) {
        object.visible = false;
        return;
      }
      object.visible = true;
      if (object instanceof Mesh && object.material) {
        const material = Array.isArray(object.material) ? object.material[0] : object.material;
        if (!(material instanceof MeshStandardMaterial)) return;
        material.color.copy(selectedNodeNames.has(object.name) ? new Color("#d94841") : new Color("#d7dad3"));
        material.emissive.copy(selectedNodeNames.has(object.name) ? new Color("#241413") : new Color("#000000"));
        material.emissiveIntensity = selectedNodeNames.has(object.name) ? 0.35 : 0;
        material.metalness = 0.1;
        material.roughness = 0.8;
      }
    });
  }, [hiddenNodeNames, isolatedNodeNames, nodeNameToOccurrence, scene, selectedNodeNames]);

  React.useEffect(() => {
    if (!fitMode) return;
    const targetNames = fitMode === "selection" ? selectedNodeNames : undefined;
    fitCameraToObjects(camera, controlsRef.current as OrbitControlsHandle | null, scene, targetNames);
  }, [camera, fitMode, fitSequence, scene, selectedNodeNames]);

  React.useEffect(() => {
    fitCameraToObjects(camera, controlsRef.current as OrbitControlsHandle | null, scene);
  }, [camera, scene]);

  return (
    <>
      <ambientLight intensity={0.9} />
      <directionalLight intensity={1.2} position={[6, 8, 6]} />
      <directionalLight intensity={0.4} position={[-6, 4, -4]} />
      <primitive
        object={scene}
        onClick={(event) => {
          event.stopPropagation();
          const clickedName = event.object.name;
          const occurrenceId = nodeNameToOccurrence.get(clickedName);
          if (occurrenceId) onSelectOccurrence(occurrenceId);
        }}
      />
      <OrbitControls ref={controlsRef} />
      <gridHelper args={[200, 20, "#d7dad3", "#eceee9"]} />
    </>
  );
}

export interface ViewerCanvasProps {
  viewer: ViewerModel;
  selectedOccurrenceIds: string[];
  hiddenOccurrenceIds: string[];
  isolatedOccurrenceId: string | null;
  onSelectOccurrence: (occurrenceId: string) => void;
  fitMode: "model" | "selection" | "reset" | null;
  fitSequence: number;
}

export function ViewerCanvas({
  fitMode,
  fitSequence,
  hiddenOccurrenceIds,
  isolatedOccurrenceId,
  onSelectOccurrence,
  selectedOccurrenceIds,
  viewer,
}: ViewerCanvasProps) {
  if (viewer.state === "failed") {
    return <ErrorState description={viewer.stateMessage} title="Viewer failed" />;
  }

  if (viewer.state === "metadata_missing") {
    return <ErrorState description={viewer.stateMessage} title="Viewer fail-closed" />;
  }

  if (viewer.state === "processing") {
    return <EmptyState description={viewer.stateMessage} title="Processing" />;
  }

  if (viewer.file.kind !== "3d") {
    return (
      <div className="h-full min-h-[480px] overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--background-surface)]">
        {viewer.contentUrl ? (
          <iframe className="h-full min-h-[480px] w-full border-0" src={viewer.contentUrl} title={viewer.file.originalName} />
        ) : (
          <EmptyState description="No preview or content URL is available for this file." title="Preview unavailable" />
        )}
      </div>
    );
  }

  if (!viewer.modelUrl) {
    return <ErrorState description="GLTF content is missing for this viewer session." title="Model unavailable" />;
  }

  return (
    <div className="h-full min-h-[560px] overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[linear-gradient(180deg,#f7f7f5_0%,#eceee9_100%)]">
      <Canvas camera={{ position: [10, 10, 10], fov: 45 }}>
        <React.Suspense fallback={<Html center>Loading model...</Html>}>
          <ModelScene
            fitMode={fitMode}
            fitSequence={fitSequence}
            hiddenOccurrenceIds={hiddenOccurrenceIds}
            isolatedOccurrenceId={isolatedOccurrenceId}
            modelUrl={viewer.modelUrl}
            nodes={viewer.nodes}
            onSelectOccurrence={onSelectOccurrence}
            selectedOccurrenceIds={selectedOccurrenceIds}
          />
        </React.Suspense>
      </Canvas>
    </div>
  );
}
