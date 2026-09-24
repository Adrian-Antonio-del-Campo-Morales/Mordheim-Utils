import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

// One lint config for the React surface: the web application's sources and its
// suite, which lives in the repository test tree. It sits at the workspace root
// because flat config only lints files below its own directory. The TypeScript
// packages suite (tests/typescript) is typechecked but not linted, as before.
export default tseslint.config(
  { ignores: ["**/dist/**", "**/coverage/**", "**/node_modules/**"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["apps/warband-manager-web/src/**/*.{ts,tsx}", "tests/web/**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
);
