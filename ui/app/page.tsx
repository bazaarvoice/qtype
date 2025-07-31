import ApiDemo from "@/components/api-demo";

export default function Home() {
  return (
    <div className="font-sans min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            QType Frontend
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
