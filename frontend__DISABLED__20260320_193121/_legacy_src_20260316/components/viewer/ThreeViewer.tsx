"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { Canvas, ThreeEvent, useThree } from "@react-three/fiber";
import { Environment, OrbitControls, OrthographicCamera, useGLTF } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

export type RenderMode = "shaded" | "shadedEdges" | "xray" | "wireframe" | "pbr";
export type ProjectionMode = "perspective" | "orthographic";

export type ViewerNode = {
  id: string;
  name: string;
  type: string;
  visible: boolean;
};

export type ViewerPartGroup = {
  partId: string;
  nodeIds: string[];
};

type ViewerProps = {
  url: string;
  renderMode?: RenderMode;
  projection?: ProjectionMode;
  interactionMode?: "rotate" | "pan";
  clip?: boolean;
  explode?: boolean;
  explodeFactor?: number;
  explodeGroups?: ViewerPartGroup[];
  clipOffset?: number;
  clipAxis?: "x" | "y" | "z" | "free";
  hiddenNodes?: Set<string>;
  selectedId?: string | null;
  measureEnabled?: boolean;
  onNodes?: (nodes: ViewerNode[]) => void;
  onSelect?: (node: ViewerNode | null) => void;
  onMeasure?: (distance: number | null, points: [THREE.Vector3, THREE.Vector3] | null) => void;
  onScreenshotReady?: (fn: () => string | null) => void;
  cameraPreset?: "iso" | "front" | "top" | "right";
  onCameraPresetChange?: (preset: "iso" | "front" | "top" | "right") => void;
  fitRequestKey?: number;
  zoomRequest?: { key: number; direction: "in" | "out" };
};

const EDGE_THRESHOLD_ANGLE = 30;
const EDGE_KEY = "__scx_edge";
const MIN_BOUNDS_EXTENT = 1e-6;
const EMIT_TRAVERSE_NODES = true;

type MeshBounds = {
  box: THREE.Box3;
  extent: number;
};

function medianExtent(values: number[]) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor((sorted.length - 1) / 2)] ?? sorted[0];
}

function getRenderableBounds(scene: THREE.Object3D) {
  const candidates: MeshBounds[] = [];
  scene.updateMatrixWorld(true);

  scene.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (!mesh.isMesh || !mesh.geometry) return;
    const geometry = mesh.geometry as THREE.BufferGeometry;
    if (!geometry.boundingBox) geometry.computeBoundingBox();
    if (!geometry.boundingBox) return;

    const worldBounds = geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
    if (
      !Number.isFinite(worldBounds.min.x) ||
      !Number.isFinite(worldBounds.min.y) ||
      !Number.isFinite(worldBounds.min.z) ||
      !Number.isFinite(worldBounds.max.x) ||
      !Number.isFinite(worldBounds.max.y) ||
      !Number.isFinite(worldBounds.max.z)
    ) {
      return;
    }

    const size = worldBounds.getSize(new THREE.Vector3());
    const extent = Math.max(size.x, size.y, size.z);
    if (!Number.isFinite(extent) || extent < MIN_BOUNDS_EXTENT) return;

    candidates.push({
      box: worldBounds,
      extent,
    });
  });

  if (!candidates.length) return null;

  const typicalExtent = medianExtent(candidates.map((item) => item.extent));
  const extentLimit = Math.max(typicalExtent * 25, typicalExtent + 0.001, 1);
  const filtered = candidates.filter((item) => item.extent <= extentLimit);
  const active = filtered.length > 0 ? filtered : candidates;

  const box = new THREE.Box3();
  active.forEach((item) => {
    box.union(item.box);
  });

  return box.isEmpty() ? null : box;
}

function fitCameraToScene(camera: THREE.Camera, scene: THREE.Object3D, controls?: OrbitControlsImpl | null) {
  const box = getRenderableBounds(scene);
  if (!box || box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const safeRadius = Math.max(sphere.radius, 0.001);

  if (camera instanceof THREE.PerspectiveCamera) {
    const halfFovY = (camera.fov * Math.PI) / 360;
    const halfFovX = Math.atan(Math.tan(halfFovY) * camera.aspect);
    const fitHeightDistance = safeRadius / Math.sin(Math.max(halfFovY, 0.0001));
    const fitWidthDistance = safeRadius / Math.sin(Math.max(halfFovX, 0.0001));
    let distance = Math.max(fitHeightDistance, fitWidthDistance);
    if (!Number.isFinite(distance) || distance <= 0) distance = maxDim;
    distance *= 1.08;
    const dir = camera.position.clone().sub(center).normalize();
    camera.position.copy(center.clone().add(dir.multiplyScalar(distance)));
    camera.near = Math.max(distance / 100, 0.01);
    camera.far = distance * 100;
    camera.updateProjectionMatrix();
  } else if (camera instanceof THREE.OrthographicCamera) {
    const pad = 1.2;
    camera.zoom = 1;
    camera.left = (-maxDim * pad) / 2;
    camera.right = (maxDim * pad) / 2;
    camera.top = (maxDim * pad) / 2;
    camera.bottom = (-maxDim * pad) / 2;
    camera.position.set(center.x + maxDim, center.y + maxDim, center.z + maxDim);
    camera.near = -maxDim * 10;
    camera.far = maxDim * 10;
    camera.updateProjectionMatrix();
  }

  if (controls) {
    controls.target.copy(center);
    controls.update();
  }
}

function SceneModel({
  url,
  renderMode = "shadedEdges",
  projection = "perspective",
  interactionMode = "rotate",
  clip = false,
  explode = false,
  explodeFactor = 0,
  explodeGroups,
  clipOffset = 0,
  clipAxis = "y",
  hiddenNodes,
  selectedId,
  measureEnabled,
  onNodes,
  onSelect,
  onMeasure,
  cameraPreset = "iso",
  fitRequestKey = 0,
  zoomRequest,
}: ViewerProps) {
  const { scene } = useGLTF(url, true);
  const { camera, invalidate } = useThree();
  const fittedRef = useRef(false);
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const baseMeshPositionsRef = useRef<Map<string, THREE.Vector3>>(new Map());
  const [measurePoints, setMeasurePoints] = useState<[THREE.Vector3, THREE.Vector3] | null>(null);
  const lastNodesHashRef = useRef<string | null>(null);

  const plane = useMemo(() => {
    const normal =
      clipAxis === "x"
        ? new THREE.Vector3(-1, 0, 0)
        : clipAxis === "z"
        ? new THREE.Vector3(0, 0, -1)
        : clipAxis === "free"
        ? new THREE.Vector3(-0.56, -0.78, -0.23)
        : new THREE.Vector3(0, -1, 0);
    return new THREE.Plane(normal.normalize(), clipOffset);
  }, [clipOffset, clipAxis]);

  useEffect(() => {
    if (!onNodes || !EMIT_TRAVERSE_NODES) return;
    const nodes: ViewerNode[] = [];
    scene.traverse((obj) => {
      nodes.push({ id: obj.uuid, name: (obj.name || obj.type || obj.uuid).trim(), type: obj.type, visible: obj.visible });
    });
    const hash = nodes.map((n) => `${n.id}:${n.visible ? "1" : "0"}`).join("|");
    if (hash !== lastNodesHashRef.current) {
      lastNodesHashRef.current = hash;
      onNodes(nodes);
    }
  }, [scene, onNodes]);

  useEffect(() => {
    // Stabil shading for STL-like sources: always refresh normals once after load.
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.geometry) return;
      const geometry = mesh.geometry as THREE.BufferGeometry;
      geometry.computeVertexNormals();
      geometry.normalizeNormals();
      geometry.attributes.normal.needsUpdate = true;
    });
  }, [scene]);

  useEffect(() => {
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.material) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach((m) => {
        const mat = m as THREE.MeshStandardMaterial;
        if (!mat.userData._base) {
          mat.userData._base = {
            color: mat.color?.clone(),
            emissive: mat.emissive?.clone(),
            emissiveIntensity: mat.emissiveIntensity,
            opacity: mat.opacity,
            transparent: mat.transparent,
            wireframe: mat.wireframe,
            metalness: mat.metalness,
            roughness: mat.roughness,
            side: mat.side,
            depthWrite: mat.depthWrite,
          };
        }
        const base = mat.userData._base;
        if (base?.color) mat.color.copy(base.color);
        if (base?.emissive) mat.emissive.copy(base.emissive);
        mat.emissiveIntensity = base?.emissiveIntensity ?? 1;
        mat.opacity = base?.opacity ?? mat.opacity;
        mat.transparent = base?.transparent ?? mat.transparent;
        mat.wireframe = base?.wireframe ?? mat.wireframe;
        mat.metalness = base?.metalness ?? mat.metalness ?? 0;
        mat.roughness = base?.roughness ?? mat.roughness ?? 1;
        mat.side = base?.side ?? THREE.FrontSide;
        mat.depthWrite = base?.depthWrite ?? true;

        if (renderMode === "wireframe") {
          mat.wireframe = true;
        } else if (renderMode === "xray") {
          mat.transparent = true;
          mat.opacity = 0.2;
          mat.depthWrite = false;
          mat.side = THREE.DoubleSide;
        } else if (renderMode === "pbr") {
          mat.wireframe = false;
          mat.transparent = false;
          mat.opacity = 1;
          mat.metalness = Math.max(base?.metalness ?? 0, 0.2);
          mat.roughness = Math.min(base?.roughness ?? 0.8, 0.55);
        } else {
          mat.wireframe = false;
        }
        mat.needsUpdate = true;
      });
    });
  }, [scene, renderMode]);

  useEffect(() => {
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.geometry) return;
      const host = mesh as THREE.Mesh & { userData: Record<string, unknown> };
      let edge = host.userData[EDGE_KEY] as THREE.LineSegments | undefined;
      if (!edge) {
        const edgeGeom = new THREE.EdgesGeometry(mesh.geometry as THREE.BufferGeometry, EDGE_THRESHOLD_ANGLE);
        const edgeMat = new THREE.LineBasicMaterial({
          color: "#3f4f62",
          transparent: true,
          opacity: 0.52,
          depthTest: true,
          depthWrite: false,
        });
        edge = new THREE.LineSegments(edgeGeom, edgeMat);
        edge.renderOrder = 2;
        edge.raycast = () => null;
        host.add(edge);
        host.userData[EDGE_KEY] = edge;
      }

      const edgeMat = edge.material as THREE.LineBasicMaterial;
      const showEdges = renderMode === "shadedEdges" || renderMode === "xray";
      edge.visible = showEdges;
      edgeMat.depthTest = renderMode !== "xray";
      edgeMat.opacity = renderMode === "xray" ? 0.35 : 0.52;
      edgeMat.needsUpdate = true;
    });
  }, [scene, renderMode]);

  useEffect(() => {
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.material) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach((m) => {
        const mat = m as THREE.MeshStandardMaterial;
        mat.clippingPlanes = clip ? [plane] : [];
        mat.clipIntersection = true;
        mat.needsUpdate = true;
      });
    });
  }, [scene, clip, plane]);

  useEffect(() => {
    scene.traverse((obj) => {
      if (hiddenNodes && hiddenNodes.has(obj.uuid)) obj.visible = false;
      else obj.visible = true;
    });
    if (!onNodes || !EMIT_TRAVERSE_NODES) return;
    const nextNodes: ViewerNode[] = [];
    scene.traverse((obj) => {
      nextNodes.push({ id: obj.uuid, name: (obj.name || obj.type || obj.uuid).trim(), type: obj.type, visible: obj.visible });
    });
    const hash = nextNodes.map((n) => `${n.id}:${n.visible ? "1" : "0"}`).join("|");
    if (hash === lastNodesHashRef.current) return;
    lastNodesHashRef.current = hash;
    onNodes(nextNodes);
  }, [scene, hiddenNodes, onNodes]);

  useEffect(() => {
    return () => {
      controlsRef.current?.dispose();
      scene.traverse((obj) => {
        const host = obj as THREE.Object3D & {
          geometry?: THREE.BufferGeometry;
          material?: THREE.Material | THREE.Material[];
          userData?: Record<string, unknown>;
        };
        const edge = host.userData?.[EDGE_KEY] as THREE.LineSegments | undefined;
        if (edge) {
          (edge.geometry as THREE.BufferGeometry | undefined)?.dispose?.();
          if (Array.isArray(edge.material)) {
            edge.material.forEach((material) => material.dispose());
          } else {
            edge.material?.dispose?.();
          }
          if (host.userData) {
            delete host.userData[EDGE_KEY];
          }
        }
        host.geometry?.dispose?.();
        if (Array.isArray(host.material)) {
          host.material.forEach((material) => material.dispose());
        } else {
          host.material?.dispose?.();
        }
      });
    };
  }, [scene]);

  useEffect(() => {
    const box = getRenderableBounds(scene);
    if (!box || box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const objectById = new Map<string, THREE.Object3D>();
    scene.traverse((obj) => {
      objectById.set(obj.uuid, obj);
    });

    const effectiveExplode = Math.max(0, Math.min(1, explodeFactor > 0 ? explodeFactor : explode ? 1 : 0));
    const activeGroups = Array.isArray(explodeGroups)
      ? explodeGroups.filter((group) => Array.isArray(group.nodeIds) && group.nodeIds.length > 0)
      : [];

    if (activeGroups.length === 0 || effectiveExplode <= 0) {
      baseMeshPositionsRef.current.forEach((base, nodeId) => {
        const obj = objectById.get(nodeId);
        if (obj) obj.position.copy(base);
      });
      scene.updateMatrixWorld(true);
      invalidate();
      return;
    }

    const modelSize = box.getSize(new THREE.Vector3());
    const modelScale = Math.max(modelSize.length(), 1);
    const touched = new Set<string>();

    activeGroups.forEach((group) => {
      const groupObjects = group.nodeIds
        .map((nodeId) => objectById.get(nodeId))
        .filter((obj): obj is THREE.Object3D => Boolean(obj));
      if (!groupObjects.length) return;

      const partBounds = new THREE.Box3();
      groupObjects.forEach((obj) => partBounds.expandByObject(obj));
      if (partBounds.isEmpty()) return;

      const partCenter = partBounds.getCenter(new THREE.Vector3());
      const dir = partCenter.sub(center);
      if (dir.lengthSq() < 1e-8) dir.set(0, 1, 0);
      else dir.normalize();

      const partSize = partBounds.getSize(new THREE.Vector3());
      const partScale = Math.max(partSize.length(), modelScale * 0.02, 0.5);
      const offset = dir.multiplyScalar(Math.max(partScale * 0.35, modelScale * 0.08) * effectiveExplode);

      groupObjects.forEach((obj) => {
        if (!baseMeshPositionsRef.current.has(obj.uuid)) {
          baseMeshPositionsRef.current.set(obj.uuid, obj.position.clone());
        }
        const base = baseMeshPositionsRef.current.get(obj.uuid) || obj.position.clone();
        obj.position.copy(base.clone().add(offset));
        touched.add(obj.uuid);
      });
    });

    baseMeshPositionsRef.current.forEach((base, nodeId) => {
      if (touched.has(nodeId)) return;
      const obj = objectById.get(nodeId);
      if (obj) obj.position.copy(base);
    });

    scene.updateMatrixWorld(true);
    invalidate();
  }, [scene, explode, explodeFactor, explodeGroups, invalidate]);

  useEffect(() => {
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.material) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      mats.forEach((m) => {
        const mat = m as THREE.MeshStandardMaterial;
        const base = mat.userData._base;
        if (base?.emissive) mat.emissive.copy(base.emissive);
        if (selectedId && obj.uuid === selectedId) {
          mat.emissive = new THREE.Color("#19b58a");
          mat.emissiveIntensity = 0.6;
        } else if (base?.emissive) {
          mat.emissiveIntensity = 1.0;
        }
        mat.needsUpdate = true;
      });
    });
  }, [scene, selectedId]);

  useEffect(() => {
    fittedRef.current = false;
    baseMeshPositionsRef.current.clear();
  }, [url, projection]);

  useEffect(() => {
    if (!measureEnabled) {
      const timeoutId = window.setTimeout(() => {
        setMeasurePoints(null);
      }, 0);
      onMeasure?.(null, null);
      return () => window.clearTimeout(timeoutId);
    }
    return undefined;
  }, [measureEnabled, onMeasure]);

  useEffect(() => {
    if (fittedRef.current) return;
    fitCameraToScene(camera, scene, controlsRef.current);
    fittedRef.current = true;
    invalidate();
  }, [scene, camera, invalidate]);

  useEffect(() => {
    if (!controlsRef.current) return;
    const box = getRenderableBounds(scene);
    if (!box || box.isEmpty()) return;

    if (cameraPreset === "iso") {
      fitCameraToScene(camera, scene, controlsRef.current);
      invalidate();
      return;
    }

    fitCameraToScene(camera, scene, controlsRef.current);
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(camera.position.distanceTo(center), 2);
    const dir =
      cameraPreset === "front"
        ? new THREE.Vector3(0, 0, 1)
        : cameraPreset === "top"
        ? new THREE.Vector3(0, 1, 0)
        : new THREE.Vector3(1, 0, 0);
    camera.position.copy(center.clone().add(dir.multiplyScalar(radius)));
    controlsRef.current.target.copy(center);
    controlsRef.current.update();
    invalidate();
  }, [cameraPreset, camera, scene, invalidate]);

  useEffect(() => {
    if (!fitRequestKey || !controlsRef.current) return;
    fitCameraToScene(camera, scene, controlsRef.current);
    invalidate();
  }, [fitRequestKey, camera, scene, invalidate]);

  useEffect(() => {
    if (!zoomRequest?.key || !controlsRef.current) return;

    const controls = controlsRef.current;
    if (camera instanceof THREE.OrthographicCamera) {
      const factor = zoomRequest.direction === "in" ? 1.2 : 0.83;
      camera.zoom = THREE.MathUtils.clamp(camera.zoom * factor, 0.2, 20);
      camera.updateProjectionMatrix();
      controls.update();
      invalidate();
      return;
    }

    const target = controls.target.clone();
    const offset = camera.position.clone().sub(target);
    const factor = zoomRequest.direction === "in" ? 0.84 : 1.19;
    camera.position.copy(target.add(offset.multiplyScalar(factor)));
    controls.update();
    invalidate();
  }, [zoomRequest, camera, invalidate]);

  const handlePick = (event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation();
    const obj = event.object as THREE.Object3D | undefined;
    if (!obj) return;
    const node: ViewerNode = {
      id: obj.uuid,
      name: obj.name || obj.type,
      type: obj.type,
      visible: obj.visible,
    };
    onSelect?.(node);

    if (measureEnabled && event.point) {
      const p = event.point.clone();
      setMeasurePoints((prev) => {
        if (!prev) {
          onMeasure?.(null, null);
          return [p, p];
        }
        const next: [THREE.Vector3, THREE.Vector3] = [prev[0], p];
        const dist = next[0].distanceTo(next[1]);
        onMeasure?.(dist, next);
        return next;
      });
    }
  };

  return (
    <>
      <primitive object={scene} onPointerDown={handlePick} />
      {measurePoints ? <MeasureLine points={measurePoints} /> : null}
      <OrbitControls
        ref={controlsRef}
        enablePan={interactionMode === "pan"}
        enableZoom
        enableRotate={interactionMode !== "pan"}
        makeDefault
      />
    </>
  );
}

function ScreenshotCapture({ onReady }: { onReady?: (fn: () => string | null) => void }) {
  const { gl } = useThree();
  useEffect(() => {
    if (!onReady) return;
    onReady(() => {
      try {
        return gl.domElement.toDataURL("image/png");
      } catch {
        return null;
      }
    });
  }, [gl, onReady]);
  return null;
}

export function ThreeViewer(props: ViewerProps) {
  const projection = props.projection ?? "perspective";
  const renderMode = props.renderMode ?? "shadedEdges";
  const [cameraPreset, setCameraPreset] = useState<"iso" | "front" | "top" | "right">(props.cameraPreset ?? "iso");
  const [canvasEpoch, setCanvasEpoch] = useState(0);
  const [contextLost, setContextLost] = useState(false);
  const detachContextListenersRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    setCameraPreset(props.cameraPreset ?? "iso");
  }, [props.cameraPreset]);

  useEffect(() => {
    return () => {
      detachContextListenersRef.current?.();
      useGLTF.clear(props.url);
    };
  }, [props.url]);

  return (
    <div className="relative h-full w-full bg-white">
      <Canvas
        key={`${props.url}:${canvasEpoch}`}
        camera={{ position: [2, 2, 2], fov: 45 }}
        shadows
        dpr={[1, 1.5]}
        resize={{ scroll: false, debounce: 0 }}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
        onCreated={({ gl }) => {
          gl.localClippingEnabled = true;
          gl.setClearColor("#ffffff");
          gl.outputColorSpace = THREE.SRGBColorSpace;
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = renderMode === "pbr" ? 1.05 : 0.95;
          const canvas = gl.domElement;
          const onLost = (event: Event) => {
            event.preventDefault();
            setContextLost(true);
          };
          const onRestored = () => {
            setContextLost(false);
            setCanvasEpoch((value) => value + 1);
          };
          detachContextListenersRef.current?.();
          canvas.addEventListener("webglcontextlost", onLost, { passive: false });
          canvas.addEventListener("webglcontextrestored", onRestored);
          detachContextListenersRef.current = () => {
            canvas.removeEventListener("webglcontextlost", onLost);
            canvas.removeEventListener("webglcontextrestored", onRestored);
          };
        }}
      >
        <ambientLight intensity={renderMode === "pbr" ? 0.45 : 0.7} />
        <hemisphereLight intensity={renderMode === "pbr" ? 0.35 : 0.6} groundColor="#cbd5e1" />
        <directionalLight position={[8, 10, 6]} intensity={renderMode === "pbr" ? 1.35 : 1.0} />
        {renderMode === "pbr" ? <Environment preset="city" /> : null}
        {projection === "orthographic" ? (
          <OrthographicCamera makeDefault position={[2, 2, 2]} />
        ) : null}
        <Suspense fallback={null}>
          <SceneModel {...props} cameraPreset={cameraPreset} />
        </Suspense>
        <ScreenshotCapture onReady={props.onScreenshotReady} />
      </Canvas>
        <ViewerOrientationCube
          activePreset={cameraPreset}
          onSelect={(preset) => {
            setCameraPreset(preset);
            props.onCameraPresetChange?.(preset);
          }}
        />
      {contextLost ? (
        <div className="pointer-events-none absolute inset-0 z-30 grid place-items-center bg-white/85">
          <div className="pointer-events-auto rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-center text-sm text-amber-800">
            <div>WebGL context was lost.</div>
            <button
              type="button"
              className="mt-2 rounded-lg border border-amber-400 bg-white px-3 py-1 text-xs font-semibold text-amber-700"
              onClick={() => {
                setContextLost(false);
                setCanvasEpoch((value) => value + 1);
              }}
            >
              Reload viewer
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MeasureLine({ points }: { points: [THREE.Vector3, THREE.Vector3] }) {
  const geom = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setFromPoints(points);
    return g;
  }, [points]);
  return (
    <line>
  <primitive object={geom} attach="geometry" />
  <lineBasicMaterial attach="material" color="#19b58a" />
</line>

  );
}

function ViewerOrientationCube({
  activePreset,
  onSelect,
}: {
  activePreset: "iso" | "front" | "top" | "right";
  onSelect: (preset: "iso" | "front" | "top" | "right") => void;
}) {
  return (
    <div className="absolute bottom-4 right-4 z-20 select-none">
      <div className="rounded-xl border border-[#d6dde5] bg-white/95 p-1.5 shadow-[0_8px_18px_rgba(15,23,42,0.14)]">
        <div className="grid grid-cols-2 gap-1">
          {[
            { key: "front", label: "Front" },
            { key: "right", label: "Right" },
            { key: "top", label: "Top" },
            { key: "iso", label: "Iso" },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onSelect(item.key as "iso" | "front" | "top" | "right")}
              className={[
                "h-8 rounded-md border px-2 text-xs font-medium",
                activePreset === item.key
                  ? "border-[#1d4ed8] bg-[#eaf2ff] text-[#1e40af]"
                  : "border-[#d1dae6] bg-white text-[#334155] hover:bg-[#f8fafc]",
              ].join(" ")}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
