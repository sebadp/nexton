import { usePendingResponses } from "@/hooks"
import { ResponseList } from "@/components/responses"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function Responses() {
  const { data, isLoading } = usePendingResponses(0, 50)

  const pendingResponses = data?.items.filter((r) => r.status === "pending") || []
  const approvedResponses = data?.items.filter((r) => r.status === "approved") || []
  const declinedResponses = data?.items.filter((r) => r.status === "declined") || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Responses</h1>
        <p className="text-muted-foreground">
          Review and approve AI-generated responses
        </p>
      </div>

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">
            Pending ({pendingResponses.length})
          </TabsTrigger>
          <TabsTrigger value="approved">
            Approved ({approvedResponses.length})
          </TabsTrigger>
          <TabsTrigger value="declined">
            Declined ({declinedResponses.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="mt-4">
          <ResponseList responses={pendingResponses} isLoading={isLoading} />
        </TabsContent>

        <TabsContent value="approved" className="mt-4">
          <ResponseList responses={approvedResponses} isLoading={isLoading} />
        </TabsContent>

        <TabsContent value="declined" className="mt-4">
          <ResponseList responses={declinedResponses} isLoading={isLoading} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
