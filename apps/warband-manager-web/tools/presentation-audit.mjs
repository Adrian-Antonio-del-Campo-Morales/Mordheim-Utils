import ts from "typescript";
import { readFileSync, readdirSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { auditPresentationTypes, createPresentationProgram } from "./presentation-type-audit.mjs";
import { createPresentationFlowAudit } from "./presentation-flow-audit.mjs";

const attributes = new Set(["title", "alt", "placeholder", "aria-label", "aria-description", "aria-valuetext", "aria-placeholder", "aria-roledescription", "aria-braillelabel", "aria-brailleroledescription", "data-label", "data-tooltip", "data-disabled-reason", "data-disabled-tooltip", "data-title", "data-status", "label"]);
const unsafeProperties = new Set(["id", "item_id", "profile_id", "band_id", "tag", "tags", "message", "applied_label", "roll_history", "profile_name", "warband_type"]);
const resolvers = new Set(["knowledgeName", "knowledgeText", "knowledgeDescription", "resolveName", "resolveNameText", "localizedLabel", "readableValue", "resourceAmount", "translate", "advanceResultText", "recordText", "legacyText", "unavailableText", "itemName"]);
// Only structural native attributes may bypass presentation validation. Unknown
// attributes are review findings, including future browser/custom extensions.
const structuralAttributes = new Set("key ref id className htmlFor role type name disabled checked defaultChecked selected multiple required readOnly autoFocus autoComplete tabIndex hidden inert open href target rel download width height rows cols min max step pattern inputMode form method action accept acceptCharset encType colSpan rowSpan scope xmlns viewBox d fill stroke strokeWidth cx cy r x y x1 y1 x2 y2 points transform focusable preserveAspectRatio aria-hidden aria-expanded aria-controls aria-describedby aria-labelledby aria-details aria-errormessage aria-live aria-atomic aria-busy aria-current aria-selected aria-checked aria-disabled aria-required aria-invalid aria-pressed aria-modal aria-haspopup aria-level aria-valuemin aria-valuemax aria-valuenow aria-posinset aria-setsize".split(" "));

/** Inventory every text sink syntactically; checks are not a language detector. */
export function inspectPresentation(source, filename = "component.tsx", semantic = {}) {
  const file = semantic.file ?? ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const sinks = [];
  const findings = [];
  const outputAdapters = new Set();
  const typedLabelComponents = new Set();
  for (const statement of file.statements) {
    if (ts.isImportDeclaration(statement) && ts.isStringLiteral(statement.moduleSpecifier) && ["/common/NumberStepper", "/dice/DiceResolver"].some((suffix) => statement.moduleSpecifier.text.endsWith(suffix))) {
      const bindings = statement.importClause?.namedBindings;
      if (bindings && ts.isNamedImports(bindings)) for (const binding of bindings.elements) {
        if (["NumberStepper", "DiceResolver"].includes(binding.propertyName?.text ?? binding.name.text)) typedLabelComponents.add(binding.name.text);
      }
    }
    if (ts.isImportDeclaration(statement) && ts.isStringLiteral(statement.moduleSpecifier) && statement.moduleSpecifier.text.endsWith("/review-exports")) {
      const bindings = statement.importClause?.namedBindings;
      if (bindings && ts.isNamedImports(bindings) && bindings.elements.some((binding) => ["ledgerText", "rosterSummaryText"].includes(binding.propertyName?.text ?? binding.name.text))) {
        findings.push({ file: filename, line: file.getLineAndCharacterOfPosition(statement.getStart(file)).line + 1, reason: "unlocalized-export", expression: statement.getText(file) });
      }
    }
    if (!ts.isImportDeclaration(statement) || !ts.isStringLiteral(statement.moduleSpecifier) || !statement.moduleSpecifier.text.endsWith("/presentation-output")) continue;
    const bindings = statement.importClause?.namedBindings;
    if (bindings && ts.isNamedImports(bindings)) for (const binding of bindings.elements) {
      if ((binding.propertyName?.text ?? binding.name.text) === "presentationOutput") outputAdapters.add(binding.name.text);
    }
  }
  const declarations = new Map();
  const destructured = new Map();
  const collect = (node) => {
    if (ts.isFunctionDeclaration(node) && node.name && node.body) {
      declarations.set(node.name.text, [...(declarations.get(node.name.text) ?? []), node]);
    }
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer) {
      const values = declarations.get(node.name.text) ?? [];
      values.push(node.initializer);
      declarations.set(node.name.text, values);
    }
    if (ts.isVariableDeclaration(node) && ts.isObjectBindingPattern(node.name) && node.initializer) {
      for (const binding of node.name.elements) {
        if (ts.isIdentifier(binding.name)) destructured.set(binding.name.text, { owner: node.initializer, key: binding.propertyName?.getText(file) ?? binding.name.text, node: binding });
      }
    }
    ts.forEachChild(node, collect);
  };
  collect(file);
  const indirectWriter = (node, seen = new Set()) => {
    if (!node || seen.has(node)) return false;
    const next = new Set(seen).add(node);
    if (ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) return /^(?:write|writeln|setAttribute|setAttributeNS|append|prepend|replaceChildren|createTextNode|insertAdjacentText|insertAdjacentHTML|fillText|strokeText|drawText|cell|multiCell|alert|confirm|prompt|setHTML|setHTMLUnsafe)$/.test(property(node) ?? "");
    if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "bind") return indirectWriter(node.expression.expression, next);
    if (ts.isIdentifier(node)) {
      if ((declarations.get(node.text) ?? []).some((value) => indirectWriter(value, next))) return true;
      const binding = destructured.get(node.text);
      if (binding && /^(?:write|writeln|setAttribute|append|prepend|createTextNode|fillText|strokeText)$/.test(binding.key)) return true;
    }
    return false;
  };
  // JSX control flow is not itself text. Its leaf outputs are visited below.
  const validatedOutput = (node) => {
    if (!node) return true;
    if (ts.isIdentifier(node) && node.text === "undefined") return true;
    if (semantic.checker) {
      const structural = (type) => type.isUnion() ? type.types.every(structural) :
        Boolean(type.flags & (ts.TypeFlags.Undefined | ts.TypeFlags.Null | ts.TypeFlags.BooleanLike)) ||
        (type.getSymbol()?.name === "ReactElement" && type.getSymbol().declarations?.some((declaration) => declaration.getSourceFile().fileName.replaceAll("\\", "/").includes("/@types/react/")));
      if (structural(semantic.checker.getTypeAtLocation(node))) return true;
    }
    if (ts.isParenthesizedExpression(node)) return validatedOutput(node.expression);
    if (ts.isJsxElement(node) || ts.isJsxFragment(node) || ts.isJsxSelfClosingElement(node)) return true;
    if ([ts.SyntaxKind.NullKeyword, ts.SyntaxKind.FalseKeyword, ts.SyntaxKind.TrueKeyword].includes(node.kind)) return true;
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && outputAdapters.has(node.expression.text)) return true;
    if (ts.isConditionalExpression(node)) return validatedOutput(node.whenTrue) && validatedOutput(node.whenFalse);
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) return validatedOutput(node.right);
    if (ts.isCallExpression(node)) {
      const called = ts.isParenthesizedExpression(node.expression) ? node.expression.expression : node.expression;
      const callback = ts.isArrowFunction(called) || ts.isFunctionExpression(called) ? called
        : ts.isPropertyAccessExpression(called) && called.name.text === "map" ? node.arguments[0]
        : ts.isPropertyAccessExpression(called) && called.expression.getText(file) === "Array" && called.name.text === "from" ? node.arguments[1]
        : undefined;
      if (!callback || (!ts.isArrowFunction(callback) && !ts.isFunctionExpression(callback))) return false;
      if (!ts.isBlock(callback.body)) return validatedOutput(callback.body);
      const returns = [];
      const scan = (child) => { if (ts.isReturnStatement(child)) returns.push(child.expression); else if (!ts.isFunctionLike(child)) ts.forEachChild(child, scan); };
      ts.forEachChild(callback.body, scan);
      return returns.length > 0 && returns.every(validatedOutput);
    }
    return false;
  };
  const resolving = new Set();
  const argumentsByParameter = new Map();
  const location = (node) => ({ file: filename, line: file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1 });
  const guiLocation = (node) => {
    let parent = node;
    while (parent && !ts.isJsxOpeningElement(parent) && !ts.isJsxSelfClosingElement(parent) && !ts.isJsxElement(parent)) parent = parent.parent;
    return parent ? (ts.isJsxElement(parent) ? parent.openingElement.tagName : parent.tagName).getText(file) : undefined;
  };
  // One finding per sink. A cut after reaching a raw origin reports the origin and
  // marks it `truncated`; only a cut that reached no origin at all is an
  // `incomplete-text-flow`, because that is the case where nothing is demonstrated.
  // Emitting both reasons for the same sink duplicated 72 of the 76 cuts and hid
  // which outputs genuinely lacked any origin; no sink loses its finding.
  const inspectFlow = (node, expression) => {
    if (!semantic.trace) return;
    const result = semantic.trace(expression);
    const entry = { ...location(node), element: guiLocation(node), expression: expression.getText(file) };
    if (result.origins.length) findings.push({ ...entry, reason: "raw-text-flow", origins: result.origins, ...(result.truncated ? { truncated: true, incomplete: result.incomplete } : {}) });
    else if (result.truncated) findings.push({ ...entry, reason: "incomplete-text-flow", incomplete: result.incomplete });
  };
  const review = (node, kind, expression, reason) => {
    const entry = { ...location(node), element: guiLocation(node), kind, expression: expression.getText(file) };
    sinks.push(entry);
    findings.push({ ...entry, reason });
    inspectFlow(node, expression);
  };
  const branded = (node) => {
    if (!semantic.checker) return false;
    const safe = (type) => type.isUnion() ? type.types.every(safe)
      : Boolean(type.flags & (ts.TypeFlags.Undefined | ts.TypeFlags.Null))
        || semantic.checker.getPropertiesOfType(type).some((property) => /__(?:@)?(?:uiTextBrand|formattedTextBrand|enumTextBrand|resolvedTextBrand|catalogueTextBrand)\b/.test(property.name));
    return safe(semantic.checker.getTypeAtLocation(node));
  };
  const property = (node) => ts.isPropertyAccessExpression(node) ? node.name.text : ts.isElementAccessExpression(node) && node.argumentExpression && ts.isStringLiteral(node.argumentExpression) ? node.argumentExpression.text : undefined;
  const inspectExpression = (node) => {
    if (ts.isIdentifier(node) && argumentsByParameter.has(node.text)) {
      const argument = argumentsByParameter.get(node.text);
      argumentsByParameter.delete(node.text);
      inspectExpression(argument);
      argumentsByParameter.set(node.text, argument);
      return;
    }
    if (ts.isIdentifier(node) && destructured.has(node.text)) {
      const binding = destructured.get(node.text);
      if (unsafeProperties.has(binding.key)) findings.push({ ...location(binding.node), reason: "raw-system-value", expression: binding.node.getText(file) });
      return;
    }
    if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) || ts.isJsxFragment(node)) return;
    if (ts.isArrowFunction(node) || ts.isFunctionExpression(node) || ts.isFunctionDeclaration(node)) {
      if (!node.body) return;
      if (ts.isBlock(node.body)) {
        const returns = (child) => { if (ts.isReturnStatement(child) && child.expression) inspectExpression(child.expression); else if (!ts.isFunctionLike(child)) ts.forEachChild(child, returns); };
        ts.forEachChild(node.body, returns);
      } else inspectExpression(node.body);
      return;
    }
    if (ts.isBinaryExpression(node)) {
      if (node.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) { inspectExpression(node.right); return; }
      if (![ts.SyntaxKind.PlusToken, ts.SyntaxKind.QuestionQuestionToken, ts.SyntaxKind.BarBarToken].includes(node.operatorToken.kind)) return;
    }
    if (ts.isConditionalExpression(node)) { inspectExpression(node.whenTrue); inspectExpression(node.whenFalse); return; }
    if (ts.isIdentifier(node) && declarations.has(node.text) && !resolving.has(node.text)) {
      resolving.add(node.text);
      declarations.get(node.text).forEach(inspectExpression);
      resolving.delete(node.text);
      return;
    }
    if (ts.isCallExpression(node)) {
      // The imported adapter's argument is checked against the opaque union by
      // TypeScript. IDs used to resolve it are not themselves visible values.
      if (ts.isIdentifier(node.expression) && outputAdapters.has(node.expression.text)) return;
      const name = ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : ts.isIdentifier(node.expression) ? node.expression.text : "";
      const local = declarations.get(name);
      if (local?.length === 1 && (ts.isArrowFunction(local[0]) || ts.isFunctionDeclaration(local[0])) && !resolving.has(name)) {
        resolving.add(name);
        const previousArguments = new Map(argumentsByParameter);
        local[0].parameters.forEach((parameter, index) => {
          if (ts.isIdentifier(parameter.name) && node.arguments[index]) argumentsByParameter.set(parameter.name.text, node.arguments[index]);
        });
        inspectExpression(local[0]);
        argumentsByParameter.clear();
        previousArguments.forEach((value, key) => argumentsByParameter.set(key, value));
        resolving.delete(name);
        return;
      }
      if (resolvers.has(name)) return;
      if (name === "Number" || (ts.isPropertyAccessExpression(node.expression) && node.expression.expression.getText(file) === "Math")) return;
      if (["map", "flatMap"].includes(name)) { node.arguments.forEach(inspectExpression); return; }
      if (["filter", "find", "some", "every", "includes", "sort", "reduce", "get", "has"].includes(name)) return;
    }
    if (unsafeProperties.has(property(node))) findings.push({ ...location(node), reason: "raw-system-value", expression: node.getText(file) });
    if (ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) {
      const owner = node.expression;
      const candidates = ts.isIdentifier(owner) ? declarations.get(owner.text) : [owner];
      for (const candidate of candidates ?? []) {
        if (!ts.isObjectLiteralExpression(candidate)) continue;
        const member = candidate.properties.find((member) => member.name?.getText(file).replace(/^["']|["']$/g, "") === property(node));
        if (member && ts.isPropertyAssignment(member)) inspectExpression(member.initializer);
        if (member && ts.isShorthandPropertyAssignment(member)) inspectExpression(member.name);
      }
    }
    // Member content is checked here; selecting a property does not render the
    // other fields of its owner or the key used for a numeric lookup.
    if (ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) return;
    if (ts.isAsExpression(node) && (node.type.kind === ts.SyntaxKind.AnyKeyword || /(?:LocalizedText|PresentationText|ResolvedKbText)/.test(node.type.getText(file)))) findings.push({ ...location(node), reason: "presentation-cast", expression: node.getText(file) });
    ts.forEachChild(node, inspectExpression);
  };
  const record = (node, kind, expression = node) => {
    sinks.push({ ...location(node), element: guiLocation(node), kind, expression: expression.getText(file) });
    inspectFlow(node, expression);
    // Forwarding a validated label retains its brand until the child adapter.
    if (ts.isJsxAttribute(node) && node.name.text === "label" && typedLabelComponents.has(node.parent.parent.tagName?.getText(file))) return;
    const writerMethod = ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : undefined;
    const typedPdf = filename.replaceAll("\\", "/") === "src/features/export/warband-pdf.ts";
    let enclosing = node.parent;
    while (enclosing && !ts.isClassDeclaration(enclosing)) enclosing = enclosing.parent;
    const pdfAdapter = typedPdf && writerMethod === "drawText" && enclosing?.name?.text === "Sheet";
    const typedPdfCall = typedPdf && ["cell", "multiCell"].includes(writerMethod);
    // The bootstrap accessibility adapter only mirrors the already-audited
    // data-disabled-reason on the same control; it cannot introduce text.
    const mirroredReason = filename.replaceAll("\\", "/") === "src/main.tsx"
      && expression.getText(file) === "control.dataset.disabledReason"
      && ((writerMethod === "setAttribute" && node.expression.expression.getText(file) === "control" && node.arguments[0]?.text === "aria-description")
        || (ts.isBinaryExpression(node) && node.left.getText(file) === "control.dataset.disabledTooltip"));
    if (!pdfAdapter && !typedPdfCall && !mirroredReason && !validatedOutput(expression)) {
      findings.push({ ...location(node), element: guiLocation(node), kind, reason: "unvalidated-output", expression: expression.getText(file) });
    }
    inspectExpression(expression);
  };
  const visit = (node) => {
    if (semantic.strict) {
      if (ts.isJsxExpression(node) && node.expression && ts.isBinaryExpression(node.expression) && node.expression.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) {
        const left = node.expression.left;
        const unsafeGuard = (type) => type.isUnion() ? type.types.some(unsafeGuard) : Boolean(type.flags & (ts.TypeFlags.StringLike | ts.TypeFlags.NumberLike | ts.TypeFlags.BigIntLike | ts.TypeFlags.Any | ts.TypeFlags.Unknown));
        if (semantic.checker ? unsafeGuard(semantic.checker.getTypeAtLocation(left)) : !ts.isBinaryExpression(left) && ![ts.SyntaxKind.TrueKeyword, ts.SyntaxKind.FalseKeyword].includes(left.kind)) review(node, "conditional-text", left, "unclassified-render-guard");
      }
      if (ts.isJsxSpreadAttribute(node)) review(node, "spread-props", node.expression, "unclassified-spread");
      if (ts.isJsxAttribute(node) && node.initializer) {
        const tag = node.parent.parent.tagName.getText(file), name = node.name.text;
        const expression = ts.isJsxExpression(node.initializer) ? node.initializer.expression ?? node.initializer : node.initializer;
        const intrinsic = /^[a-z][a-z0-9-]*$/.test(tag);
        if (name === "dangerouslySetInnerHTML") review(node, "html-injection", expression, "unclassified-html");
        else if (name.toLowerCase() === "srcdoc") review(node, "embedded-document", expression, "unclassified-html");
        else if (tag.includes("-") || ["animate", "set", "animateTransform"].includes(tag)) review(node, "dynamic-attribute", expression, "unclassified-element-attribute");
        else if (name === "style") {
          if (!ts.isObjectLiteralExpression(expression)) review(node, "inline-style", expression, "unclassified-style");
          else for (const prop of expression.properties) {
            if (ts.isSpreadAssignment(prop) || (prop.name && ts.isComputedPropertyName(prop.name))) review(prop, "inline-style", prop, "unclassified-style");
            else if (prop.name?.getText(file).replace(/["']/g, "") === "content") review(prop, "css-text", prop, "unclassified-style-content");
          }
        }
        else if (intrinsic && ["value", "defaultValue"].includes(name)) {
          const typeAttribute = node.parent.properties.find((prop) => ts.isJsxAttribute(prop) && prop.name.text === "type");
          const inputType = typeAttribute?.initializer && ts.isStringLiteral(typeAttribute.initializer) ? typeAttribute.initializer.text : typeAttribute ? undefined : "text";
          if (["option", "select"].includes(tag) || (tag === "input" && ["hidden", "checkbox", "radio"].includes(inputType))) {
            sinks.push({ ...location(node), element: tag, kind: "selection-value", classification: "non-display-identity", expression: expression.getText(file) });
          } else if (validatedOutput(expression)) record(node, "control-value", expression);
          else review(node, "control-value", expression, "unclassified-control-value");
        } else if (!intrinsic && !attributes.has(name) && !["key", "ref"].includes(name) && !/^on[A-Z]/.test(name)) {
          // Custom props can contain indirect labels, nested row models or callbacks.
          // Their names are not evidence that they are non-visible.
          if (branded(expression) || validatedOutput(expression)) sinks.push({ ...location(node), element: tag, kind: "component-prop", classification: "validated-presentation", expression: expression.getText(file) });
          else review(node, "component-prop", expression, "unclassified-component-prop");
        } else if (intrinsic && name === "children") record(node, "children-prop", expression);
        else if (intrinsic && name.startsWith("data-") && !attributes.has(name)) review(node, "custom-data", expression, "unclassified-data-attribute");
        else if (intrinsic && !attributes.has(name) && !structuralAttributes.has(name) && !/^on[A-Z]/.test(name)) review(node, "native-attribute", expression, "unclassified-native-attribute");
      }
      if (ts.isCallExpression(node)) {
        const name = ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : node.expression.getText(file);
        if (["createElement", "cloneElement", "jsx", "jsxs", "jsxDEV"].includes(name)) {
          // Native createElement only creates an empty node; subsequent writes are audited.
          const native = ts.isPropertyAccessExpression(node.expression) && node.expression.expression.getText(file) === "document" && name === "createElement";
          if (!native) review(node, "dynamic-element", node, "unclassified-dynamic-element");
        }
        if (["createTextNode", "fillText", "strokeText"].includes(name)) record(node, "text-writer", node.arguments[0] ?? node);
        if (["append", "prepend", "replaceChildren", "replaceWith", "insertAdjacentElement"].includes(name)) review(node, "dynamic-dom", node, "unclassified-dom-insertion");
        if (ts.isIdentifier(node.expression) && indirectWriter(node.expression)) review(node, "aliased-writer", node, "unclassified-aliased-writer");
        if (["call", "apply"].includes(name) && ts.isPropertyAccessExpression(node.expression) && indirectWriter(node.expression.expression)) review(node, "indirect-writer", node, "unclassified-aliased-writer");
        if (name === "setAttributeNS") {
          const attr = node.arguments[1];
          if (!attr || !ts.isStringLiteral(attr) || attributes.has(attr.text)) record(node, "dom-attribute", node.arguments[2] ?? node);
        }
        if (["setHTML", "setHTMLUnsafe", "createContextualFragment", "parseFromString"].includes(name)) review(node, "html-parser", node, "unclassified-html");
        if (ts.isPropertyAccessExpression(node.expression) && ["Object.assign", "Object.defineProperty", "Object.defineProperties", "Reflect.set"].includes(node.expression.getText(file))) review(node, "indirect-write", node, "unclassified-indirect-write");
        if (["insertRule", "addRule", "replaceSync", "setProperty"].includes(name)) review(node, "dynamic-css", node, "unclassified-style");
        if (ts.isElementAccessExpression(node.expression)) review(node, "dynamic-call", node, "unclassified-computed-call");
        if (["eval", "Function", "importScripts"].includes(name)) review(node, "dynamic-code", node, "unclassified-dynamic-code");
        if (["render", "createPortal"].includes(name) && node.arguments[0]) record(node, "react-root", node.arguments[0]);
        if (node.expression.kind === ts.SyntaxKind.ImportKeyword && (!ts.isStringLiteral(node.arguments[0]) || !node.arguments[0].text.startsWith("."))) review(node, "dynamic-import", node, "unclassified-dynamic-code");
      }
      if (ts.isNewExpression(node) && ["Function", "Worker", "SharedWorker"].includes(node.expression.getText(file))) review(node, "dynamic-code", node, "unclassified-dynamic-code");
      if (ts.isBinaryExpression(node) && [ts.SyntaxKind.EqualsToken, ts.SyntaxKind.PlusEqualsToken].includes(node.operatorToken.kind)) {
        const name = property(node.left);
        if ((ts.isPropertyAccessExpression(node.left) || ts.isElementAccessExpression(node.left)) && ["dataset", "style"].includes(property(node.left.expression))) review(node, "indirect-dom-property", node.right, "unclassified-property-write");
        if (ts.isElementAccessExpression(node.left) && !ts.isStringLiteral(node.left.argumentExpression)) review(node, "dynamic-write", node, "unclassified-computed-write");
        else if (["value", "defaultValue", "placeholder", "alt", "ariaLabel", "outerHTML", "nodeValue", "data"].includes(name)) review(node, "dom-property", node.right, "unclassified-property-write");
        else if (node.operatorToken.kind === ts.SyntaxKind.PlusEqualsToken && ["textContent", "innerText", "innerHTML", "outerHTML", "title"].includes(name)) record(node, "dom-write", node.right);
        if (ts.isPropertyAccessExpression(node.left) && ts.isPropertyAccessExpression(node.left.expression) && node.left.expression.name.text === "style" && ["content", "cssText"].includes(name)) review(node, "dynamic-css", node.right, "unclassified-style-content");
      }
    }
    if (ts.isAsExpression(node) && node.type.kind === ts.SyntaxKind.AnyKeyword) {
      findings.push({ ...location(node), reason: "presentation-cast", expression: node.getText(file) });
    }
    if (ts.isAsExpression(node) && /\b(?:UiText|LocalizedText|PresentationText|ResolvedKbText|FormattedText|EnumText)\b/.test(node.type.getText(file))) {
      const ownedUiConstructor = filename.replaceAll("\\", "/") === "src/features/campaign/i18n-core.ts" && node.type.getText(file) === "UiText";
      const ownedValueConstructor = filename.replaceAll("\\", "/") === "src/features/campaign/presentation-values.ts" && node.type.getText(file) === "FormattedText";
      const ownedEnumConstructor = filename.replaceAll("\\", "/") === "src/features/campaign/presentation-enums.ts" && node.type.getText(file) === "EnumText";
      if (!ownedUiConstructor && !ownedValueConstructor && !ownedEnumConstructor) findings.push({ ...location(node), reason: "presentation-cast", expression: node.getText(file) });
    }
    if (ts.isJsxText(node) && node.text.trim()) record(node, "jsx-text");
    if (ts.isJsxExpression(node) && node.expression && !ts.isJsxAttribute(node.parent)) record(node, "jsx-expression", node.expression);
    if (ts.isJsxAttribute(node) && attributes.has(node.name.text) && node.initializer) record(node, "attribute", ts.isJsxExpression(node.initializer) ? node.initializer.expression ?? node.initializer : node.initializer);
    if (ts.isCallExpression(node)) {
      const name = ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : node.expression.getText(file);
      if (["drawText", "cell", "multiCell", "alert", "confirm", "prompt"].includes(name)) record(node, "document-or-dialog", node.arguments[["cell", "multiCell"].includes(name) ? 2 : 0] ?? node);
      if (name === "setAttribute" && node.arguments[0]) {
        const attribute = node.arguments[0];
        if (!ts.isStringLiteral(attribute) || attributes.has(attribute.text)) record(node, "dom-attribute", node.arguments[1] ?? node);
      }
      if (["insertAdjacentHTML", "insertAdjacentText"].includes(name)) record(node, "dom-write", node.arguments[1] ?? node);
      if (["write", "writeln"].includes(name)) for (const argument of node.arguments) record(node, "dom-write", argument);
      if (name === "prompt" && node.arguments[1]) record(node, "dialog-default", node.arguments[1]);
    }
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.EqualsToken && ["textContent", "innerText", "innerHTML", "title"].includes(property(node.left))) record(node, "dom-write", node.right);
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.EqualsToken && ts.isPropertyAccessExpression(node.left) && ts.isPropertyAccessExpression(node.left.expression) && node.left.expression.name.text === "dataset") {
      const attribute = "data-" + node.left.name.text.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
      if (attributes.has(attribute)) record(node, "dom-attribute", node.right);
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return { sinks, findings: [...new Map(findings.map((finding) => [JSON.stringify(finding), finding])).values()] };
}

/** CSS content can only expose validated attributes or declared decorative symbols. */
export function inspectCssPresentation(source, filename = "styles.css") {
  const sinks = [], findings = [];
  // Preserve offsets while removing comments; escaped property names and imports
  // cannot silently evade the small CSS grammar supported by this detector.
  source = source.replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\r\n]/g, " "));
  for (const match of source.matchAll(/\\|@import\b/gi)) findings.push({ file: filename, line: source.slice(0, match.index).split("\n").length, reason: "unclassified-css-syntax", expression: match[0] });
  const symbols = new Set(["", "◆", "▤", "✦", "⚔", "✓", "+"]);
  for (const match of source.matchAll(/(?:^|[;{])\s*content\s*:\s*([^;}]+)/gi)) {
    const expression = match[1].trim();
    const sink = { file: filename, line: source.slice(0, match.index).split("\n").length, kind: "css-content", expression };
    sinks.push(sink);
    const quoted = /^(?:"([^"\\]*)"|'([^'\\]*)')$/.exec(expression);
    const attribute = /^attr\(([-\w]+)\)$/.exec(expression);
    if (!["none", "normal"].includes(expression) && !(quoted && symbols.has(quoted[1] ?? quoted[2])) && !(attribute && attributes.has(attribute[1]))) {
      findings.push({ ...sink, reason: "unvalidated-css-content" });
    }
  }
  return { sinks, findings };
}

function files(path, strict = false) {
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) => entry.isDirectory() ? files(resolve(path, entry.name), strict) : (strict ? /\.(?:[cm]?[jt]sx?|css|html|svg)$/ : /\.(tsx?|css)$/).test(entry.name) && !/\.test\./.test(entry.name) && entry.name !== "test-setup.ts" ? [resolve(path, entry.name)] : []);
}

export function audit(root, { strict = false, deep = false } = {}) {
  const sinks = [], findings = [];
  const program = createPresentationProgram(root), checker = program.getTypeChecker();
  const trace = strict ? createPresentationFlowAudit(program, root, deep ? { maxSteps: 2500, maxDepth: 80 } : {}) : undefined;
  const paths = files(resolve(root, "src"), strict);
  if (strict) {
    paths.push(resolve(root, "index.html"));
    // Imported workspace modules may render text without living under src/.
    for (const file of program.getSourceFiles()) if (!file.isDeclarationFile && !file.fileName.includes("node_modules") && !/\.test\./.test(file.fileName) && !file.fileName.endsWith("test-setup.ts")) paths.push(file.fileName);
    if (existsSync(resolve(root, "public"))) paths.push(...files(resolve(root, "public"), true));
  }
  for (const path of new Set(paths.map((path) => resolve(path)))) {
    const name = relative(root, path).replaceAll("\\", "/");
    const source = readFileSync(path, "utf8");
    if (strict && !/\.(tsx?|css)$/.test(path)) {
      const entry = { file: name, line: 1, kind: "unclassified-source", expression: "Revisar esta fuente de GUI: no está cubierta por el analizador TypeScript/JSX/CSS." };
      sinks.push(entry); findings.push({ ...entry, reason: "unclassified-source-format" });
      continue;
    }
    if (path.endsWith(".css")) {
      const result = inspectCssPresentation(source, name);
      sinks.push(...result.sinks); findings.push(...result.findings);
      continue;
    }
    const result = inspectPresentation(source, name, { file: program.getSourceFile(path), checker, strict, trace });
    sinks.push(...result.sinks); findings.push(...result.findings);
  }
  findings.push(...auditPresentationTypes(root, program));
  if (strict) for (const diagnostic of ts.getPreEmitDiagnostics(program)) {
    findings.push({ file: diagnostic.file ? relative(root, diagnostic.file.fileName).replaceAll("\\", "/") : "tsconfig.json", line: diagnostic.file && diagnostic.start !== undefined ? diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start).line + 1 : 1, reason: "compiler-error", expression: ts.flattenDiagnosticMessageText(diagnostic.messageText, " ") });
  }
  return { sinks, findings };
}

export function guiReport(result) {
  const cell = (value) => String(value ?? "—").replaceAll("|", "\\|").replace(/\r?\n/g, " ").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  const counts = new Map();
  for (const row of result.findings) counts.set(row.reason, (counts.get(row.reason) ?? 0) + 1);
  return ["# Auditoría de textos de la GUI", "", `${result.sinks.length} puntos inventariados; ${result.findings.length} incidencias o salidas sin clasificar.`, "", "Una salida sin clasificar no es una fuga confirmada: el analizador no puede demostrar su protección. Revisar origen y destino antes de corregirla. No ocultar incidencias mediante casts o supresiones.", "", "## Resumen", "", ...[...counts].map(([reason, count]) => `- ${reason}: ${count}`), "", "## Ubicaciones", "", "| Archivo | Línea | Elemento | Motivo | Expresión | Origen y recorrido |", "| --- | --- | --- | --- | --- | --- |", ...result.findings.map((row) => `| ${cell(row.file)} | ${row.line} | ${cell(row.element)} | ${cell(row.reason)} | ${cell(row.expression)} | ${cell(row.origins ? row.origins.map((origin) => `${origin.file}:${origin.line} (${origin.expression}) via ${origin.path.map((step) => `${step.file}:${step.line}`).join(" → ")}`).join("; ") + (row.truncated ? " [recorrido truncado: no enumera todos los orígenes]" : "") : undefined)} |`), "", "Alcance: código web TypeScript/JSX/CSS analizado y tipos del proyecto. No prueba calidad lingüística, estados ejecutados, bibliotecas externas, HTML externo ni cualquier construcción dinámica de JavaScript. Los adaptadores autorizados siguen requiriendo revisión y pruebas.", ""].join("\n");
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const strict = process.argv.includes("--strict") || process.argv.includes("--deep");
  const deep = process.argv.includes("--deep");
  const result = audit(root, { strict: strict || deep, deep });
  const output = resolve(root, `../../build/generated/${deep ? "gui-text-audit-deep" : strict ? "gui-text-audit" : "presentation-audit"}.json`);
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
  if (strict) writeFileSync(output.replace(/\.json$/, ".md"), guiReport(result));
  console.log(`${result.sinks.length} presentation sinks; ${result.findings.length} ${strict ? "findings requiring review" : "raw-system findings"}. ${output}`);
  if (strict) console.log(`Readable report: ${output.replace(/\.json$/, ".md")}`);
  if (process.argv.includes("--check") && result.findings.length) process.exitCode = 1;
}
