import ts from "typescript";
import { resolve, relative } from "node:path";

const constructors = new Map([
  ["src/features/campaign/i18n-core.ts", "uiTextBrand"],
  ["src/features/campaign/presentation-values.ts", "formattedTextBrand"],
  ["src/features/campaign/presentation-enums.ts", "enumTextBrand"],
]);
const brands = /__(?:@)?(?:uiTextBrand|formattedTextBrand|enumTextBrand|resolvedTextBrand|catalogueTextBrand)\b/;

/** Uses resolved types, so renamed imports, aliases and typeof cannot forge text. */
export function inspectPresentationTypes(program, file, root) {
  const checker = program.getTypeChecker();
  const filename = relative(root, file.fileName).replaceAll("\\", "/");
  const findings = [];
  const fail = (node, reason) => findings.push({ file: filename, line: file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1, reason, expression: node.getText(file) });
  const textBrands = (type, seen = new Set()) => {
    if (seen.has(type)) return [];
    seen.add(type);
    if (type.isUnionOrIntersection()) return type.types.flatMap((child) => textBrands(child, seen));
    const properties = checker.getPropertiesOfType(type);
    const own = properties.filter((property) => brands.test(property.name)).map((property) => property.name);
    if (own.length || (type.flags & (ts.TypeFlags.StringLike | ts.TypeFlags.NumberLike | ts.TypeFlags.BooleanLike))) return own;
    // Inspect stored values, not methods on services that legitimately resolve text.
    return properties.flatMap((property) => {
      if (property.flags & ts.SymbolFlags.Method) return [];
      const declaration = property.valueDeclaration ?? property.declarations?.[0];
      return declaration ? textBrands(checker.getTypeOfSymbolAtLocation(property, declaration), seen) : [];
    });
  };
  const visit = (node) => {
    if (node.kind === ts.SyntaxKind.AnyKeyword) fail(node, "presentation-any");
    if (ts.isAsExpression(node) || ts.isTypeAssertionExpression(node)) {
      if (node.type.getText(file) === "const") { ts.forEachChild(node, visit); return; }
      const targetBrands = textBrands(checker.getTypeAtLocation(node));
      const owned = constructors.get(filename);
      if (targetBrands.length && (!owned || targetBrands.some((brand) => !brand.includes(owned)))) fail(node, "presentation-type-forgery");
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  for (const match of file.text.matchAll(/@ts-(?:ignore|nocheck|expect-error)|eslint-disable/g)) {
    findings.push({ file: filename, line: file.getLineAndCharacterOfPosition(match.index).line + 1, reason: "presentation-suppression", expression: match[0] });
  }
  return findings;
}

export function createPresentationProgram(root) {
  const config = ts.readConfigFile(resolve(root, "tsconfig.json"), ts.sys.readFile);
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, root);
  return ts.createProgram(parsed.fileNames, parsed.options);
}

export function auditPresentationTypes(root, program = createPresentationProgram(root)) {
  return program.getSourceFiles().filter((file) => {
    const name = relative(root, file.fileName).replaceAll("\\", "/");
    return !file.isDeclarationFile && !name.includes("node_modules/") && !name.includes(".test.") && !name.endsWith("test-setup.ts");
  }).flatMap((file) => inspectPresentationTypes(program, file, root));
}
