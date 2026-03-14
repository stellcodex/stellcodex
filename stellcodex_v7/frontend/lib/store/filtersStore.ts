export type ListFiltersState = {
  search: string;
  status: string;
  sort: string;
};

const defaultState: ListFiltersState = {
  search: "",
  status: "all",
  sort: "updated_desc",
};

let state: ListFiltersState = defaultState;

export function getFiltersState() {
  return state;
}

export function setFiltersState(next: Partial<ListFiltersState>) {
  state = { ...state, ...next };
}

export function resetFiltersState() {
  state = defaultState;
}
