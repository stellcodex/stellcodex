import type { FileSummary } from "@/lib/contracts/files";
import type { ViewerOccurrenceNode, ViewerSummary } from "@/lib/contracts/viewer";
import { getViewerState } from "@/lib/utils/status";

type RawRecord = Record<string, unknown>;

function childIds(rawChildren: unknown) {
  if (!Array.isArray(rawChildren)) return [];
  return rawChildren
    .map((child) => {
      if (typeof child === "string") return child;
      if (child && typeof child === "object") {
        const row = child as RawRecord;
        return typeof row.occurrence_id === "string"
          ? row.occurrence_id
          : typeof row.id === "string"
          ? row.id
          : null;
      }
      return null;
    })
    .filter((value): value is string => Boolean(value));
}

export function mapAssemblyTree(input: unknown): ViewerOccurrenceNode[] {
  const rows = Array.isArray(input) ? input : [];
  const flat = rows
    .map((item) => (item && typeof item === "object" ? (item as RawRecord) : null))
    .filter((value): value is RawRecord => Boolean(value));
  const byId = new Map<string, RawRecord>();
  const referenced = new Set<string>();

  flat.forEach((row) => {
    const nodeId =
      typeof row.occurrence_id === "string"
        ? row.occurrence_id
        : typeof row.id === "string"
        ? row.id
        : "";
    if (!nodeId) return;
    byId.set(nodeId, row);
    childIds(row.children).forEach((childId) => referenced.add(childId));
  });

  const buildNode = (nodeId: string, path: string[]): ViewerOccurrenceNode | null => {
    const row = byId.get(nodeId);
    if (!row) return null;
    const label =
      (typeof row.display_name === "string" && row.display_name) ||
      (typeof row.name === "string" && row.name) ||
      nodeId;
    const children = childIds(row.children)
      .map((childId) => buildNode(childId, [...path, label]))
      .filter((child): child is ViewerOccurrenceNode => Boolean(child));
    return {
      nodeId,
      label,
      occurrencePath: [...path, label].join(" / "),
      visible: true,
      selected: false,
      childCount: children.length,
      renderBindings: Array.isArray(row.gltf_nodes)
        ? row.gltf_nodes.filter((item): item is string => typeof item === "string")
        : [],
      children,
    };
  };

  const roots = [...byId.keys()].filter((key) => !referenced.has(key));
  return roots.map((rootId) => buildNode(rootId, [])).filter((node): node is ViewerOccurrenceNode => Boolean(node));
}

export function countOccurrences(nodes: ViewerOccurrenceNode[]): number {
  return nodes.reduce((total, node) => total + 1 + countOccurrences(node.children || []), 0);
}

export function mapViewerSummary(file: FileSummary, manifest: unknown): ViewerSummary {
  const payload = (manifest && typeof manifest === "object" ? manifest : {}) as RawRecord;
  const tree = mapAssemblyTree(payload.assembly_tree);
  const hasAssemblyMeta = tree.length > 0;
  const viewerKind = file.kind === "2d" || file.kind === "doc" || file.kind === "image" ? (file.kind as "2d" | "doc" | "image") : "3d";
  const viewerUrl = file.gltfUrl || file.previewUrls?.[0] || file.originalUrl || null;

  if (viewerKind === "3d" && !hasAssemblyMeta) {
    return {
      fileId: file.fileId,
      status: "unavailable",
      hasAssemblyMeta: false,
      totalOccurrences: 0,
      assemblyTree: [],
      viewerUrl,
      viewerKind,
      unavailableReason: "Viewer unavailable: assembly metadata missing",
    };
  }

  return {
    fileId: file.fileId,
    status: viewerUrl ? getViewerState(file.status) : "unavailable",
    hasAssemblyMeta,
    totalOccurrences: countOccurrences(tree),
    assemblyTree: tree,
    viewerUrl,
    viewerKind,
    unavailableReason: viewerUrl ? null : "Viewer unavailable",
  };
}
