import { create } from "zustand"
import type { OpportunityFilters } from "@/types"

interface AppState {
  // Sidebar
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Opportunity filters
  opportunityFilters: OpportunityFilters
  setOpportunityFilters: (filters: OpportunityFilters) => void
  resetOpportunityFilters: () => void

  // Pagination
  currentPage: number
  pageSize: number
  setCurrentPage: (page: number) => void
  setPageSize: (size: number) => void
}

const defaultFilters: OpportunityFilters = {
  sort_by: "created_at",
  sort_order: "desc",
}

export const useAppStore = create<AppState>((set) => ({
  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Opportunity filters
  opportunityFilters: defaultFilters,
  setOpportunityFilters: (filters) =>
    set((state) => ({
      opportunityFilters: { ...state.opportunityFilters, ...filters },
    })),
  resetOpportunityFilters: () => set({ opportunityFilters: defaultFilters }),

  // Pagination
  currentPage: 1,
  pageSize: 10,
  setCurrentPage: (page) => set({ currentPage: page }),
  setPageSize: (size) => set({ pageSize: size, currentPage: 1 }),
}))
