import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getSettings, updateSettings } from "@/api"
import type { UpdateSettingsRequest } from "@/types"

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  })
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateSettingsRequest) => updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] })
    },
  })
}
