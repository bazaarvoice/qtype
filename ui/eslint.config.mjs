import { dirname } from "path";
import { fileURLToPath } from "url";

import pluginJs from "@eslint/js";
import pluginTs from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import importPlugin from "eslint-plugin-import";
import prettierPlugin from "eslint-plugin-prettier";
import globals from "globals";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default [
  { files: ["**/*.{js,mjs,cjs,ts,tsx}"] },
  { ignores: ["node_modules", ".next"] },
  {
    plugins: {
      "@typescript-eslint": pluginTs,
      import: importPlugin,
      prettier: prettierPlugin,
      pluginJs: pluginJs,
    },

    rules: {
      ...pluginJs.configs.recommended.rules,
      ...pluginTs.configs.recommended.rules,
      ...prettierPlugin.configs.recommended.rules,
      "no-console": "error",
      "@typescript-eslint/consistent-type-exports": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "import/order": [
        "error",
        {
          groups: [
            "builtin",
            "external",
            "internal",
            "parent",
            "sibling",
            "index",
            "type",
          ],
          "newlines-between": "always",
          alphabetize: { order: "asc", caseInsensitive: true },
          pathGroups: [
            { pattern: "{ type, @/**/types{,/**}}", group: "type" },
            { pattern: "@/**", group: "internal", position: "after" },
          ],
          pathGroupsExcludedImportTypes: ["type"],
        },
      ],
      "prettier/prettier": "error",
    },
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: __dirname,
      },
      globals: {
        ...globals.node,
        ...globals.browser,
        React: "readonly",
      },
    },
  },
];
