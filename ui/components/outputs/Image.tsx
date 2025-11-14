interface ImageProps {
  fileName: string;
  mime: string;
  bytesBase64: string;
}

function Image({
  fileName,
  mime,
  bytesBase64,
}: ImageProps): React.ReactElement {
  const cleanBase64 = (typeof bytesBase64 === "string" ? bytesBase64 : "")
    .replace(/^data:[^;]+;base64,/, "")
    .replace(/\s+/g, "")
    .replace(/[^A-Za-z0-9+/=]/g, "");

  const isImageMime = /^image\//.test(mime);
  const padding = (cleanBase64.match(/=/g) || []).length;
  const rawByteLength =
    cleanBase64.length > 0 ? (cleanBase64.length * 3) / 4 - padding : 0;

  const sizeLabel =
    rawByteLength < 1024
      ? `${rawByteLength} B`
      : rawByteLength < 1024 * 1024
        ? `${(rawByteLength / 1024).toFixed(1)} KB`
        : `${(rawByteLength / (1024 * 1024)).toFixed(2)} MB`;

  const invalid =
    !isImageMime || cleanBase64.length === 0 || cleanBase64.length % 4 !== 0;

  const dataUrl = invalid ? "" : `data:${mime};base64,${cleanBase64}`;

  const handleDownload = () => {
    if (invalid) return;
    try {
      const byteChars = atob(cleanBase64);
      const bytes = new Uint8Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i += 1) {
        bytes[i] = byteChars.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName || "image";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Ignore malformed base64 download attempts.
    }
  };

  if (invalid) {
    return (
      <div
        className={
          "inline-flex flex-col gap-1 rounded border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700"
        }
        aria-label="Invalid image data"
      >
        <span className="font-semibold">Invalid image</span>
        <span>MIME: {mime || "(none)"}</span>
      </div>
    );
  }

  return (
    <div
      className={
        `group relative flex w-full max-w-xs flex-col items-center gap-2 rounded-md ` +
        `border border-neutral-200 bg-white p-3 shadow-sm transition ` +
        `hover:shadow-md dark:border-neutral-700 dark:bg-neutral-900"`
      }
      aria-label={`Image ${fileName} size ${sizeLabel}`}
      title={`${fileName} (${sizeLabel})`}
    >
      <div className="relative flex items-center justify-center w-full">
        <img
          src={dataUrl}
          alt={fileName || "image"}
          className="h-auto max-h-64 w-auto max-w-full rounded-md object-contain"
          loading="lazy"
        />
      </div>
      <div className="flex w-full items-center justify-between text-[11px] text-neutral-600 dark:text-neutral-400">
        <span className="truncate max-w-[60%]" title={fileName}>
          {fileName}
        </span>
        <span>{sizeLabel}</span>
      </div>
      <button
        type="button"
        onClick={handleDownload}
        className="mt-1 w-full rounded bg-neutral-200 px-2 py-1 text-xs font-medium text-neutral-800 transition hover:bg-neutral-300 dark:bg-neutral-700 dark:text-neutral-100 dark:hover:bg-neutral-600"
        aria-label="Download image"
      >
        Download
      </button>
    </div>
  );
}

export { Image };
