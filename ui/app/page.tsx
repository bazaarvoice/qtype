"use client";

import { useEffect } from "react";

import { FlowTabsContainer } from "@/components/FlowTabsContainer";
import { useOpenApiSpec } from "@/lib/hooks/useApi";

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
    <div className="font-sans min-h-screen p-6 sm:p-8">
      <main className="max-w-6xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="text-center border-b pb-4">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            {pageTitle}
          </h1>
          {spec?.info?.description && (
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              {spec.info.description}
            </p>
          )}
        </div>

        <FlowTabsContainer />
      </main>
    </div>
  );
}
