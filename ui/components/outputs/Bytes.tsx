export interface BytesProps {
  fileName: string;
  mime: string;
  bytesBase64: string;
}

function Bytes({
  fileName,
  mime,
  bytesBase64,
}: BytesProps): React.ReactElement {
  const cleanBase64 = bytesBase64
    .replace(/^data:[^;]+;base64,/, "")
    .replace(/\s+/g, "")
    .replace(/[^A-Za-z0-9+/=]/g, "");

  const invalid = cleanBase64.length === 0 || cleanBase64.length % 4 !== 0;

  const paddingChars = cleanBase64.endsWith("==")
    ? 2
    : cleanBase64.endsWith("=")
      ? 1
      : 0;
  const rawLength = invalid ? 0 : (cleanBase64.length * 3) / 4 - paddingChars;

  const sizeLabel = invalid
    ? "Invalid"
    : rawLength < 1024
      ? `${rawLength} B`
      : rawLength < 1024 * 1024
        ? `${(rawLength / 1024).toFixed(1)} KB`
        : `${(rawLength / (1024 * 1024)).toFixed(2)} MB`;

  const handleDownload = () => {
    if (invalid) {
      return;
    }
    try {
      const byteChars = atob(cleanBase64);
      const byteNumbers = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i += 1) {
        byteNumbers[i] = byteChars.charCodeAt(i);
      }
      const blob = new Blob([new Uint8Array(byteNumbers)], { type: mime });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = fileName || "data.bin";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      // Silent fail on malformed base64
    }
  };

  return (
    <div
      className="group rounded border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 p-3 text-xs flex flex-col gap-2"
      title={`${fileName} (${sizeLabel})`}
      aria-label={`Bytes content ${fileName} size ${sizeLabel}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-neutral-700 dark:text-neutral-300">
          {fileName}
        </span>
        <button
          type="button"
          onClick={handleDownload}
          disabled={invalid}
          className={`px-2 py-1 rounded transition text-neutral-800 dark:text-neutral-100 ${invalid ? "cursor-not-allowed opacity-50 bg-neutral-200 dark:bg-neutral-700" : "bg-neutral-200 dark:bg-neutral-700 hover:bg-neutral-300 dark:hover:bg-neutral-600"}`}
          aria-label={invalid ? "Invalid base64" : "Download bytes file"}
        >
          {invalid ? "Invalid" : "Download"}
        </button>
      </div>
      <div className="font-mono text-neutral-600 dark:text-neutral-400 break-all">
        {cleanBase64.slice(0, 80)}
        {cleanBase64.length > 80 ? "…" : ""}
      </div>
      <div className="text-neutral-500 dark:text-neutral-400">MIME: {mime}</div>
      <div className="text-neutral-500 dark:text-neutral-400">
        Size: {sizeLabel}
      </div>
    </div>
  );
}

export { Bytes };
