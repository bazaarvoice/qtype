import React from "react";

export interface DateTimeProps {
  value: string;
  date?: boolean;
  time?: boolean;
}

const parts = {
  date: new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }),
  weekday: new Intl.DateTimeFormat(undefined, {
    weekday: "short",
  }),
  time: new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }),
};

function DateTime({
  value,
  time,
  date,
}: DateTimeProps): React.ReactElement | null {
  const isTimeOnly =
    Boolean(time) && !date && /^\d{2}:\d{2}(:\d{2})?$/.test(value);

  const normalized = isTimeOnly
    ? /^\d{2}:\d{2}$/.test(value)
      ? `${value}:00`
      : value
    : /T\d{2}:\d{2}$/.test(value)
      ? `${value}:00`
      : value;

  const fullDate = isTimeOnly ? null : new Date(normalized);

  return (
    <div
      className={
        `group inline-flex items-baseline gap-2 rounded-md border border-neutral-200 ` +
        `bg-neutral-50 px-3 py-2 text-sm text-neutral-700 shadow-sm transition ` +
        `hover:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-800 ` +
        `dark:text-neutral-200 dark:hover:bg-neutral-700`
      }
      aria-label={"Date time iso"}
    >
      {!isTimeOnly && date && fullDate && (
        <>
          <span className="font-semibold tracking-wide text-neutral-900 dark:text-neutral-100">
            {parts.weekday.format(fullDate)}
          </span>
          <span className="text-neutral-600 dark:text-neutral-300">
            {parts.date.format(fullDate)}
          </span>
        </>
      )}
      {time && (
        <span className="text-neutral-500 dark:text-neutral-400">
          @ {isTimeOnly ? normalized : parts.time.format(fullDate as Date)}
        </span>
      )}
    </div>
  );
}

export { DateTime };
