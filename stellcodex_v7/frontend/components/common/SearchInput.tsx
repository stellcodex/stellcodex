"use client";

import { useState } from "react";

type SearchInputProps = {
  placeholder?: string;
  onChange?: (value: string) => void;
};

export function SearchInput({ placeholder = "Ara", onChange }: SearchInputProps) {
  const [value, setValue] = useState("");
  return (
    <div className="flex h-inputMinH items-center gap-sp1 rounded-r1 bg-surface2 px-cardPad border-soft">
      <span className="text-icon text-fs1">⌕</span>
      <input
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          onChange?.(e.target.value);
        }}
        placeholder={placeholder}
        className="w-full bg-transparent text-fs1 text-text placeholder:text-muted focus:outline-none"
      />
    </div>
  );
}
