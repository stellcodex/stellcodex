import * as React from "react";

import { cn } from "@/lib/utils";

export interface RadioOption {
  label: string;
  value: string;
  description?: string;
}

export interface RadioGroupProps {
  name: string;
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function RadioGroup({ className, name, onChange, options, value }: RadioGroupProps) {
  return (
    <div className={cn("grid gap-2", className)}>
      {options.map((option) => (
        <label
          key={option.value}
          className="flex cursor-pointer items-start gap-3 rounded-[12px] border border-[#eeeeee] bg-white px-3 py-3"
        >
          <input
            checked={value === option.value}
            className="mt-1 h-4 w-4"
            name={name}
            onChange={() => onChange(option.value)}
            type="radio"
            value={option.value}
          />
          <span className="space-y-1">
            <span className="block text-sm font-medium">{option.label}</span>
            {option.description ? <span className="block text-sm text-[var(--foreground-muted)]">{option.description}</span> : null}
          </span>
        </label>
      ))}
    </div>
  );
}
