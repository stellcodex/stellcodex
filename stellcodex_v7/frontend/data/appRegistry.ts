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
    description: "3D modeli inceleyin ve detaylara bakın.",
  },
  {
    key: "2d",
    label: "2D DXF",
    shortLabel: "2D",
    homeLabel: "2D DXF",
    href: "/app/2d",
    icon: "2D",
    description: "DXF çizimleri görüntüleyin ve ölçülendirin.",
  },
  {
    key: "exploded",
    label: "Patlatma",
    shortLabel: "Patlatma",
    homeLabel: "Patlatma",
    href: "/app/explode",
    icon: "PT",
    description: "Patlatılmış görünümle montajı inceleyin.",
  },
  {
    key: "render",
    label: "Render",
    shortLabel: "Render",
    href: "/app/render",
    icon: "RD",
    description: "Sahne ve malzeme ayarlarıyla render alın.",
  },
  {
    key: "moldcodes",
    label: "MoldCodes",
    shortLabel: "Mold",
    href: "/app/moldcodes",
    icon: "MC",
    description: "Standart eleman kataloglarını inceleyin.",
  },
  {
    key: "qa",
    label: "QA Panel",
    shortLabel: "QA",
    href: "/app/qa",
    icon: "QA",
    description: "Hızlı kalite kontrol ve doğrulama paneli.",
  },
];
