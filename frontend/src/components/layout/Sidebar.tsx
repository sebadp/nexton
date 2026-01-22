import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  Briefcase,
  MessageSquare,
  User,
  Settings,
  Linkedin,
  AlertTriangle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAppStore } from "@/store"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { useOpportunityStats } from "@/hooks"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Opportunities", href: "/opportunities", icon: Briefcase },
  { name: "Manual Review", href: "/manual-review", icon: AlertTriangle, showBadge: true },
  { name: "Responses", href: "/responses", icon: MessageSquare },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen)
  const { data: stats } = useOpportunityStats()
  const pendingReviewCount = stats?.pending_manual_review || 0

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300",
        sidebarOpen ? "w-64" : "w-16"
      )}
    >
      <div className="flex h-16 items-center border-b px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Linkedin className="h-5 w-5 text-primary-foreground" />
          </div>
          {sidebarOpen && (
            <span className="text-lg font-semibold">LinkedIn Agent</span>
          )}
        </div>
      </div>

      <ScrollArea className="h-[calc(100vh-4rem)]">
        <nav className="flex flex-col gap-1 p-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  !sidebarOpen && "justify-center"
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {sidebarOpen && (
                <span className="flex-1">{item.name}</span>
              )}
              {item.showBadge && pendingReviewCount > 0 && (
                <Badge
                  variant="amber"
                  className={cn(
                    "px-1.5 py-0.5 text-xs",
                    !sidebarOpen && "absolute -top-1 -right-1"
                  )}
                >
                  {pendingReviewCount}
                </Badge>
              )}
            </NavLink>
          ))}
        </nav>
      </ScrollArea>
    </aside>
  )
}
