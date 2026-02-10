"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, OrthographicCamera, useGLTF } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

export type RenderMode = "shaded" | "wireframe" | "hidden";
export type ProjectionMode = "perspective" | "orthographic";

export type ViewerNode = {
  id: string;
  name: string;
  type: string;
  visible: boolean;
};

type ViewerProps = {
  url: string;
  renderMode?: RenderMode;
  projection?: ProjectionMode;
  clip?: boolean;
  clipOffset?: number;
  hiddenNodes?: Set<string>;
  selectedId?: string | null;
  measureEnabled?: boolean;
  onNodes?: (nodes: ViewerNode[]) => void;
  onSelect?: (node: ViewerNode | null) => void;
  onMeasure?: (distance: number | null, points: [THREE.Vector3, THREE.Vector3] | null) => void;
  onScreenshotReady?: (fn: () => string | null) => void;
};

function fitCameraToScene(camera: THREE.Camera, scene: THREE.Object3D, controls?: OrbitControlsImpl | null) {
  const box = new THREE.Box3().setFromObject(scene);
  if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z) || 1;

  if (camera instanceof THREE.PerspectiveCamera) {
    const fov = (camera.fov * Math.PI) / 180;
    let distance = maxDim / (2 * Math.tan(fov / 2));
    if (!Number.isFinite(distance) || distance <= 0) distance = maxDim;
    distance *= 1.6;
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
  renderMode = "shaded",
  projection = "perspective",
  clip = false,
  clipOffset = 0,
  hiddenNodes,
  selectedId,
  measureEnabled,
  onNodes,
  onSelect,
  onMeasure,
}: ViewerProps) {
  const { scene } = useGLTF(url, true);
  const { gl, camera, invalidate } = useThree();
  const fittedRef = useRef(false);
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const [measurePoints, setMeasurePoints] = useState<[THREE.Vector3, THREE.Vector3] | null>(null);
  const lastNodesHashRef = useRef<string | null>(null);

  const plane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, -1, 0), clipOffset), [clipOffset]);

  useEffect(() => {
    gl.localClippingEnabled = true;
  }, [gl]);

  useEffect(() => {
    const nodes: ViewerNode[] = [];
    scene.traverse((obj) => {
      if (obj.name) {
        nodes.push({ id: obj.uuid, name: obj.name, type: obj.type, visible: obj.visible });
      }
    });
    const hash = nodes.map((n) => `${n.id}:${n.visible ? "1" : "0"}`).join("|");
    if (hash !== lastNodesHashRef.current) {
      lastNodesHashRef.current = hash;
      onNodes?.(nodes);
    }
  }, [scene, onNodes]);

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
            opacity: mat.opacity,
            transparent: mat.transparent,
            wireframe: mat.wireframe,
          };
        }
        const base = mat.userData._base;
        if (base?.color) mat.color.copy(base.color);
        if (base?.emissive) mat.emissive.copy(base.emissive);
        mat.opacity = base?.opacity ?? mat.opacity;
        mat.transparent = base?.transparent ?? mat.transparent;
        mat.wireframe = base?.wireframe ?? mat.wireframe;

        if (renderMode === "wireframe") {
          mat.wireframe = true;
        } else if (renderMode === "hidden") {
          mat.wireframe = true;
          mat.transparent = true;
          mat.opacity = 0.25;
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
    const nextNodes: ViewerNode[] = [];
    scene.traverse((obj) => {
      if (hiddenNodes && hiddenNodes.has(obj.uuid)) obj.visible = false;
      else obj.visible = true;
      if (obj.name) {
        nextNodes.push({ id: obj.uuid, name: obj.name, type: obj.type, visible: obj.visible });
      }
    });
    const hash = nextNodes.map((n) => `${n.id}:${n.visible ? "1" : "0"}`).join("|");
    if (hash !== lastNodesHashRef.current) {
      lastNodesHashRef.current = hash;
      onNodes?.(nextNodes);
    }
  }, [scene, hiddenNodes, onNodes]);

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
  }, [url, projection]);

  useEffect(() => {
    if (!measureEnabled) {
      setMeasurePoints(null);
      onMeasure?.(null, null);
    }
  }, [measureEnabled, onMeasure]);

  useEffect(() => {
    if (fittedRef.current) return;
    fitCameraToScene(camera, scene, controlsRef.current);
    fittedRef.current = true;
    invalidate();
  }, [scene, camera, invalidate]);

  const handlePick = (event: any) => {
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
      <OrbitControls ref={controlsRef} enablePan enableZoom enableRotate makeDefault />
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
  const url = props.url;

  useEffect(() => {
    console.log("[ThreeViewer] MOUNT");
    return () => {
      console.log("[ThreeViewer] UNMOUNT");
    };
  }, []);

  useEffect(() => {
    console.log("[ThreeViewer] URL change", url);
  }, [url]);

  return (
    <div className="h-full w-full">
      <Canvas
        camera={{ position: [2, 2, 2], fov: 45 }}
        shadows
        dpr={[1, 1.5]}
        resize={{ scroll: false, debounce: 0 }}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
        onCreated={({ gl }) => {
          gl.setClearColor("#f3f2ee");
          gl.outputColorSpace = THREE.SRGBColorSpace;
        }}
      >
        <ambientLight intensity={0.7} />
        <hemisphereLight intensity={0.6} groundColor="#cbd5e1" />
        <directionalLight position={[8, 10, 6]} intensity={1.0} />
        {projection === "orthographic" ? (
          <OrthographicCamera makeDefault position={[2, 2, 2]} />
        ) : null}
        <Suspense fallback={null}>
          <SceneModel {...props} />
        </Suspense>
        <ScreenshotCapture onReady={props.onScreenshotReady} />
      </Canvas>
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
