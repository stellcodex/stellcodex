import { Button } from "@/components/ui/Button";

export function SecondaryButton(
  props: React.ComponentProps<typeof Button>
) {
  return <Button {...props} variant="secondary" />;
}
