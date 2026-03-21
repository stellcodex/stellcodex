import { SearchInput } from "@/components/primitives/SearchInput";

export interface TreeSearchProps {
  value: string;
  onChange: (value: string) => void;
}

export function TreeSearch({ onChange, value }: TreeSearchProps) {
  return <SearchInput onChange={(event) => onChange(event.target.value)} placeholder="Search occurrences" value={value} />;
}
