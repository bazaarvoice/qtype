import React from "react";

export interface DateTimeProps {
  value: string;
  showSeconds?: boolean;
  className?: string;
}

interface FormattedParts {
  date: string;
  time: string;
  weekday: string;
  iso: string;
}

function formatParts(value: string): FormattedParts | undefined {
  if (!value) {
    return undefined;
  }
  const normalized = /T\d{2}:\d{2}$/.test(value) ? `${value}:00` : value;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return undefined;
  }
  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
  const weekdayFormatter = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
  });
  const timeFormatter = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  return {
    date: dateFormatter.format(date),
    time: timeFormatter.format(date),
    weekday: weekdayFormatter.format(date),
    iso: date.toISOString(),
  };
}

function DateTime({ value }: DateTimeProps): React.ReactElement {
  const parts = formatParts(value);

  if (!parts) {
    return (
      <span
        className={
          `inline-flex items-center rounded border border-red-200 bg-red-50 px-2 py-1 ` +
          "text-xs font-medium text-red-700"
        }
      >
        Invalid date
      </span>
    );
  }

  return (
    <div
      className={
        `group inline-flex items-baseline gap-2 rounded-md border border-neutral-200 ` +
        `bg-neutral-50 px-3 py-2 text-sm text-neutral-700 shadow-sm transition ` +
        `hover:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-800 ` +
        "dark:text-neutral-200 dark:hover:bg-neutral-700"
      }
      title={parts.iso}
      aria-label={`Date time ${parts.date} ${parts.time}`}
    >
      <span className="font-semibold tracking-wide text-neutral-900 dark:text-neutral-100">
        {parts.weekday}
      </span>
      <span className="text-neutral-600 dark:text-neutral-300">
        {parts.date}
      </span>
      <span className="text-neutral-500 dark:text-neutral-400">
        @ {parts.time}
      </span>
    </div>
  );
}

export { DateTime };
