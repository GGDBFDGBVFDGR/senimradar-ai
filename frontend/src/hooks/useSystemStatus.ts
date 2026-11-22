import { useQuery } from "@tanstack/react-query";

import { getCapabilities, getHealth, getReady } from "../services/api.ts";

export function useSystemStatus() {
  const health = useQuery({
    queryKey: ["system", "health"],
    queryFn: getHealth,
  });
  const ready = useQuery({
    queryKey: ["system", "ready"],
    queryFn: getReady,
  });
  const capabilities = useQuery({
    queryKey: ["system", "capabilities"],
    queryFn: getCapabilities,
  });

  return { health, ready, capabilities };
}
