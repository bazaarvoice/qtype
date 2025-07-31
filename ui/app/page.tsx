'use client'

import { useEffect } from "react";
import { useOpenApiSpec } from "@/lib/hooks/use-api";
import ApiDemo from "@/components/api-demo";

export default function Home() {
  const { spec, isLoading } = useOpenApiSpec();
  
  // Use API title if available, otherwise fallback
  const pageTitle = spec?.info?.title || "QType Frontend";

  // Update document title when API title changes
  useEffect(() => {
    if (!isLoading) {
      document.title = pageTitle;
    }
  }, [pageTitle, isLoading]);

  return (
    <div className="font-sans min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-white"></div>
                Loading...
              </span>
            ) : (
              pageTitle
            )}
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            A Next.js frontend for your FastAPI backend
          </p>
        </div>

        <ApiDemo />
      </main>
    </div>
  );
}
