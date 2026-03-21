/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)"],
      },
      fontSize: {
        fs0: ["var(--fs-0)", { lineHeight: "var(--lh-0)", fontWeight: "var(--fw-regular)" }],
        fs1: ["var(--fs-1)", { lineHeight: "var(--lh-1)", fontWeight: "var(--fw-regular)" }],
        fs2: ["var(--fs-2)", { lineHeight: "var(--lh-2)", fontWeight: "var(--fw-medium)" }],
        fs3: ["var(--fs-3)", { lineHeight: "var(--lh-3)", fontWeight: "var(--fw-semibold)" }],
      },
      spacing: {
        sp0: "var(--sp-0)",
        sp1: "var(--sp-1)",
        sp2: "var(--sp-2)",
        sp3: "var(--sp-3)",
        sp4: "var(--sp-4)",
        sp5: "var(--sp-5)",
        pagePad: "var(--page-pad)",
        sectionGap: "var(--section-gap)",
        cardPad: "var(--card-pad)",
        cardGap: "var(--card-gap)",
        rowH: "var(--row-h)",
        btnH: "var(--btn-h)",
        inputMinH: "var(--input-min-h)",
        navH: "var(--nav-h)",
      },
      borderRadius: {
        r0: "var(--r-0)",
        r1: "var(--r-1)",
        r2: "var(--r-2)",
        r3: "var(--r-3)",
      },
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        surface2: "var(--surface-2)",
        text: "var(--text)",
        muted: "var(--muted)",
        muted2: "var(--muted-2)",
        icon: "var(--icon)",
        accent: "var(--accent)",
        accentWeak: "var(--accent-weak)",
      },
      boxShadow: {
        sh0: "var(--sh-0)",
        sh1: "var(--sh-1)",
        sh2: "var(--sh-2)",
        focus: "var(--focus)",
      },
    },
  },
  plugins: [
    function ({ addUtilities }) {
      addUtilities({
        ".border-strong": { border: "var(--b-strong)" },
        ".border-soft": { border: "var(--b-soft)" },
        ".border-t-strong": { borderTop: "var(--b-strong)" },
        ".border-b-strong": { borderBottom: "var(--b-strong)" },
        ".border-l-strong": { borderLeft: "var(--b-strong)" },
        ".border-r-strong": { borderRight: "var(--b-strong)" },
        ".border-t-soft": { borderTop: "var(--b-soft)" },
        ".border-b-soft": { borderBottom: "var(--b-soft)" },
        ".border-l-soft": { borderLeft: "var(--b-soft)" },
        ".border-r-soft": { borderRight: "var(--b-soft)" },
      });
    },
  ],
};
