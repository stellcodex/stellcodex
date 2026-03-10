export type AppRegistryItem = {
  key: string;
  label: string;
  shortLabel: string;
  homeLabel?: string;
  href: string;
  icon: string;
  description: string;
};

export const appRegistry: AppRegistryItem[] = [
  {
    key: "3d",
    label: "3D Model",
    shortLabel: "3D",
    href: "/app/3d",
    icon: "3D",
    description: "Inspect the 3D model and review the details.",
  },
  {
    key: "2d",
    label: "2D DXF",
    shortLabel: "2D",
    homeLabel: "2D DXF",
    href: "/app/2d",
    icon: "2D",
    description: "Open DXF drawings and inspect measurements.",
  },
  {
    key: "exploded",
    label: "Exploded View",
    shortLabel: "Explode",
    homeLabel: "Exploded View",
    href: "/app/explode",
    icon: "PT",
    description: "Inspect the assembly with an exploded view.",
  },
  {
    key: "render",
    label: "Render",
    shortLabel: "Render",
    href: "/app/render",
    icon: "RD",
    description: "Prepare renders with scene and material settings.",
  },
  {
    key: "moldcodes",
    label: "MoldCodes",
    shortLabel: "Mold",
    href: "/app/moldcodes",
    icon: "MC",
    description: "Browse standard component catalogs.",
  },
  {
    key: "qa",
    label: "QA Panel",
    shortLabel: "QA",
    href: "/app/qa",
    icon: "QA",
    description: "Run quick quality control and validation checks.",
  },
];
