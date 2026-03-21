import type { AppsCatalogItem } from "@/services/api";
import type { PlatformAppId } from "@/data/platformCatalog";

export type MarketplaceIntegration = {
  mode: "core" | "manifest";
  coreAppId: PlatformAppId | null;
  headline: string;
  note: string;
  primaryLabel: string;
};

const CORE_APP_ALIASES: Record<string, PlatformAppId> = {
  stellview: "viewer3d",
  stellviewer3d: "viewer3d",
  stelldraw: "viewer2d",
  stellviewer2d: "viewer2d",
  stellmesh: "mesh2d3d",
  stellmoldcodes: "moldcodes",
  stellconvert: "convert",
  stelllibrary: "library",
  stelldrive: "drive",
  stellproject: "projects",
  stellexplorer: "drive",
  stellshare: "drive",
  stellupload: "drive",
  stellstatus: "status",
  "stelladmin-lite": "admin",
};

export function resolveMarketplaceCoreAppId(slug: string): PlatformAppId | null {
  return CORE_APP_ALIASES[slug] || null;
}

export function normalizeMarketplaceCategory(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function summarizeMarketplaceCapabilities(item: AppsCatalogItem) {
  const capabilities = item.required_capabilities.length > 0 ? item.required_capabilities.join(" • ") : "No explicit capability list";
  const formats = item.supported_formats.length > 0 ? item.supported_formats.join(", ") : "No explicit format list";
  return { capabilities, formats };
}

export function getMarketplaceIntegration(item: AppsCatalogItem): MarketplaceIntegration {
  const coreAppId = resolveMarketplaceCoreAppId(item.slug);
  if (coreAppId) {
    return {
      mode: "core",
      coreAppId,
      headline: "Integrated core module",
      note: "This registry entry is delivered through the shared workspace surface for the same capability. The module is inside the platform, not a separate product.",
      primaryLabel: "Open integrated module",
    };
  }

  if (!item.enabled) {
    return {
      mode: "manifest",
      coreAppId: null,
      headline: "Registered module",
      note: "This module is registered in the marketplace and manifest system but is currently disabled by feature flags or tier policy. The manifest surface remains available for review.",
      primaryLabel: "Review manifest",
    };
  }

  return {
    mode: "manifest",
    coreAppId: null,
    headline: "Manifest-backed module",
    note: "This module is part of the platform inventory. The current surface exposes its manifest, capabilities, dependencies, and delivery state until a dedicated workflow is promoted into the workspace shell.",
    primaryLabel: "Review module",
  };
}
