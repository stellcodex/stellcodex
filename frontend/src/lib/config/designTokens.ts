export const designTokens = {
  backgrounds: {
    canvas: "var(--background-canvas)",
    shell: "var(--background-shell)",
    surface: "var(--background-surface)",
    subtle: "var(--background-subtle)",
    muted: "var(--background-muted)",
  },
  foregrounds: {
    default: "var(--foreground-default)",
    strong: "var(--foreground-strong)",
    muted: "var(--foreground-muted)",
    soft: "var(--foreground-soft)",
    inverse: "var(--foreground-inverse)",
  },
  borders: {
    default: "var(--border-default)",
    strong: "var(--border-strong)",
    muted: "var(--border-muted)",
  },
  accent: {
    default: "var(--accent-default)",
    soft: "var(--accent-soft)",
    foreground: "var(--accent-foreground)",
  },
  status: {
    success: {
      background: "var(--status-success-bg)",
      foreground: "var(--status-success-fg)",
    },
    warning: {
      background: "var(--status-warning-bg)",
      foreground: "var(--status-warning-fg)",
    },
    danger: {
      background: "var(--status-danger-bg)",
      foreground: "var(--status-danger-fg)",
    },
    info: {
      background: "var(--status-info-bg)",
      foreground: "var(--status-info-fg)",
    },
  },
  typography: {
    xs: "var(--text-xs)",
    sm: "var(--text-sm)",
    base: "var(--text-base)",
    lg: "var(--text-lg)",
    xl: "var(--text-xl)",
    "2xl": "var(--text-2xl)",
    "3xl": "var(--text-3xl)",
    regular: "var(--weight-regular)",
    medium: "var(--weight-medium)",
    semibold: "var(--weight-semibold)",
    bold: "var(--weight-bold)",
  },
  spacing: {
    1: "var(--space-1)",
    2: "var(--space-2)",
    3: "var(--space-3)",
    4: "var(--space-4)",
    5: "var(--space-5)",
    6: "var(--space-6)",
    8: "var(--space-8)",
    10: "var(--space-10)",
    12: "var(--space-12)",
  },
  radius: {
    sm: "var(--radius-sm)",
    md: "var(--radius-md)",
    lg: "var(--radius-lg)",
    xl: "var(--radius-xl)",
    "2xl": "var(--radius-2xl)",
    round: "var(--radius-round)",
  },
  shadow: {
    xs: "var(--shadow-xs)",
    sm: "var(--shadow-sm)",
    md: "var(--shadow-md)",
  },
  zIndex: {
    base: "var(--z-base)",
    dropdown: "var(--z-dropdown)",
    sticky: "var(--z-sticky)",
    overlay: "var(--z-overlay)",
    modal: "var(--z-modal)",
  },
  motion: {
    fast: "var(--motion-fast)",
    base: "var(--motion-base)",
    slow: "var(--motion-slow)",
    ease: "var(--ease-standard)",
  },
} as const;

export type DesignTokens = typeof designTokens;
