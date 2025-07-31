"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"
import { format } from "date-fns"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

import type { SchemaProperty, FlowInputValue } from '../../types/flow'

interface DatePickerInputProps {
  name: string
  property: SchemaProperty
  required: boolean
  value?: FlowInputValue
  onChange?: (name: string, value: FlowInputValue) => void
}

export default function DatePickerInput({ name, property, value, onChange, required }: DatePickerInputProps) {
  const [date, setDate] = React.useState<Date | undefined>(
    value && typeof value === 'string' ? new Date(value) : undefined
  )

  const handleDateSelect = (selectedDate: Date | undefined) => {
    setDate(selectedDate)
    
    if (selectedDate) {
      // For date type, format as YYYY-MM-DD
      const formatted = format(selectedDate, 'yyyy-MM-dd')
      onChange?.(name, formatted)
    }
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {property.title || 'Date'} {required && <span className="text-red-500">*</span>}
      </label>
      
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={"outline"}
            className={cn(
              "w-full justify-start text-left font-normal",
              !date && "text-muted-foreground"
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date ? format(date, 'PPP') : 'Select a date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0">
          <Calendar
            mode="single"
            selected={date}
            onSelect={handleDateSelect}
            initialFocus
          />
        </PopoverContent>
      </Popover>
      
      {property.description && (
        <p className="text-sm text-muted-foreground">{property.description}</p>
      )}
    </div>
  )
}
