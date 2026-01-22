import { useState } from "react"
import { X, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface TechStackEditorProps {
  technologies: string[]
  onChange: (technologies: string[]) => void
}

export function TechStackEditor({ technologies, onChange }: TechStackEditorProps) {
  const [newTech, setNewTech] = useState("")

  const handleAdd = () => {
    if (newTech.trim() && !technologies.includes(newTech.trim())) {
      onChange([...technologies, newTech.trim()])
      setNewTech("")
    }
  }

  const handleRemove = (tech: string) => {
    onChange(technologies.filter((t) => t !== tech))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          placeholder="Add technology..."
          value={newTech}
          onChange={(e) => setNewTech(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button type="button" onClick={handleAdd} size="icon">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {technologies.map((tech) => (
          <Badge key={tech} variant="secondary" className="gap-1 pr-1">
            {tech}
            <button
              type="button"
              onClick={() => handleRemove(tech)}
              className="ml-1 rounded-full p-0.5 hover:bg-muted-foreground/20"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
        {technologies.length === 0 && (
          <p className="text-sm text-muted-foreground">No technologies added</p>
        )}
      </div>
    </div>
  )
}
