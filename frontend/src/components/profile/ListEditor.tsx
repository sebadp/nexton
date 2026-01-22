import { useState } from "react"
import { X, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

interface ListEditorProps {
  items: string[]
  onChange: (items: string[]) => void
  placeholder?: string
}

export function ListEditor({ items, onChange, placeholder = "Add item..." }: ListEditorProps) {
  const [newItem, setNewItem] = useState("")

  const handleAdd = () => {
    if (newItem.trim() && !items.includes(newItem.trim())) {
      onChange([...items, newItem.trim()])
      setNewItem("")
    }
  }

  const handleRemove = (item: string) => {
    onChange(items.filter((i) => i !== item))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          placeholder={placeholder}
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button type="button" onClick={handleAdd} size="icon" variant="outline">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <ul className="space-y-1">
        {items.map((item, index) => (
          <li
            key={index}
            className="flex items-center justify-between rounded-md bg-muted px-3 py-2 text-sm"
          >
            <span>{item}</span>
            <button
              type="button"
              onClick={() => handleRemove(item)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </li>
        ))}
        {items.length === 0 && (
          <li className="text-sm text-muted-foreground">No items added</li>
        )}
      </ul>
    </div>
  )
}
