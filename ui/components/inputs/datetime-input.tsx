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
import { Input } from "@/components/ui/input"

import type { SchemaProperty, FlowInputValue } from '../../types/flow'

interface DateTimeInputProps {
  name: string
  property: SchemaProperty
  required: boolean
  value?: FlowInputValue
  onChange?: (name: string, value: FlowInputValue) => void
}

export default function DateTimeInput({ name, property, value, onChange, required }: DateTimeInputProps) {
  // Parse initial datetime value
  const parseInitialValue = (val?: string) => {
    if (!val) return { date: undefined, time: '' }
    
    const dateTime = new Date(val)
    if (isNaN(dateTime.getTime())) return { date: undefined, time: '' }
    
    return {
      date: dateTime,
      time: val.includes('T') ? val.split('T')[1]?.split('.')[0] || '' : ''
    }
  }

  const { date: initialDate, time: initialTime } = parseInitialValue(typeof value === 'string' ? value : undefined)
  
  const [date, setDate] = React.useState<Date | undefined>(initialDate)
  const [timeValue, setTimeValue] = React.useState<string>(initialTime)

  const combineDateTime = (selectedDate?: Date, time?: string) => {
    if (!selectedDate) return
    
    const dateStr = format(selectedDate, 'yyyy-MM-dd')
    const timeStr = time || '00:00:00'
    const fullDateTime = `${dateStr}T${timeStr}`
    onChange?.(name, fullDateTime)
  }

  const handleDateSelect = (selectedDate: Date | undefined) => {
    setDate(selectedDate)
    combineDateTime(selectedDate, timeValue)
  }

  const handleTimeChange = (time: string) => {
    setTimeValue(time)
    combineDateTime(date, time)
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {property.title || 'Date & Time'} {required && <span className="text-red-500">*</span>}
      </label>
      
      <div className="flex flex-col space-y-2">
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
              {date ? (
                <span>
                  {format(date, 'PPP')} 
                  {timeValue && <span className="text-muted-foreground ml-2">at {timeValue}</span>}
                </span>
              ) : (
                'Select date and time'
              )}
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
        
        <Input
          type="time"
          value={timeValue}
          onChange={(e) => handleTimeChange(e.target.value)}
          step="1"
          placeholder="HH:MM:SS"
          className="w-full"
        />
      </div>
      
      {property.description && (
        <p className="text-sm text-muted-foreground">{property.description}</p>
      )}
    </div>
  )
}
