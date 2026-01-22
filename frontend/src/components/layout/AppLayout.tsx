import { Outlet } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { Header } from "./Header"
import { useAppStore } from "@/store"
import { cn } from "@/lib/utils"

export function AppLayout() {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen)

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Header />
      <main
        className={cn(
          "pt-16 transition-all duration-300",
          sidebarOpen ? "ml-64" : "ml-16"
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
