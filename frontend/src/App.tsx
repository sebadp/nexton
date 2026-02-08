import { Suspense, lazy } from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/toaster"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { PageLoader } from "@/components/LoadingSpinner"
import { AppLayout } from "@/components/layout/AppLayout"

// Lazy load pages for better performance
const Dashboard = lazy(() => import("@/pages/Dashboard"))
const Opportunities = lazy(() => import("@/pages/Opportunities"))
const OpportunityDetail = lazy(() => import("@/pages/OpportunityDetail"))
const ManualReview = lazy(() => import("@/pages/ManualReview"))
const Responses = lazy(() => import("@/pages/Responses"))
const Profile = lazy(() => import("@/pages/Profile"))
const Settings = lazy(() => import("@/pages/Settings"))

function App() {
  return (
    <ErrorBoundary>
      <TooltipProvider>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route
              path="dashboard"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route
              path="opportunities"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Opportunities />
                </Suspense>
              }
            />
            <Route
              path="opportunities/:id"
              element={
                <Suspense fallback={<PageLoader />}>
                  <OpportunityDetail />
                </Suspense>
              }
            />
            <Route
              path="manual-review"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ManualReview />
                </Suspense>
              }
            />
            <Route
              path="responses"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Responses />
                </Suspense>
              }
            />
            <Route
              path="profile"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Profile />
                </Suspense>
              }
            />
            <Route
              path="settings"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Settings />
                </Suspense>
              }
            />
          </Route>
        </Routes>
      </TooltipProvider>
      <Toaster />
    </ErrorBoundary>
  )
}

export default App
