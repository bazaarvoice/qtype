// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from "@tailwindcss/vite";

// https://astro.build/config
export default defineConfig({
    outDir: '../qtype/interpreter/ui',  // Output to the interpreter module
    build: {
        assets: 'assets'
    },
    vite: {
        plugins: [tailwindcss()],
        define: {
            // Make environment variables available to the client
            __API_BASE_URL__: JSON.stringify(
                process.env.NODE_ENV === 'development' 
                    ? 'http://localhost:8000/'
                    : './'
            )
        }
    },
});
