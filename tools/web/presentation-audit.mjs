import ts from "typescript";
import { readFileSync, readdirSync, mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { auditPresentationTypes, createPresentationProgram, inspectPresentationTypes } from "./presentation-type-audit.mjs";
import { createPresentationFlowAudit } from "./presentation-flow-audit.mjs";

const attributes = new Set(["title", "alt", "placeholder", "aria-label", "aria-description", "aria-valuetext", "aria-placeholder", "aria-roledescription", "aria-braillelabel", "aria-brailleroledescription", "data-label", "data-tooltip", "data-disabled-reason", "data-disabled-tooltip", "data-title", "data-status", "label"]);
const unsafeProperties = new Set(["id", "item_id", "profile_id", "band_id", "tag", "tags", "message", "applied_label", "roll_history", "profile_name", "warband_type"]);
// Adapters that turn domain/system values into presentation text. Every member
// returns branded text on every path, so its lookup keys are not visible values.
// `variantName` returns `ResolvedKbText` from `recordText` (or the unavailable
// message); it was missing here, which made a non-GUI sink that takes a band id
// through it look like raw system text (§presentación).
// `abilityNameText`/`warriorAbilityName`/`conditionDetailText` are the same kind
// of resolver for captured v5 ability labels and condition details: each returns
// a resolved `ResolvedKbText` or the reader's specific unknown-reference notice,
// never the stored label.
const resolvers = new Set(["knowledgeName", "knowledgeText", "knowledgeDescription", "resolveName", "resolveNameText", "localizedLabel", "readableValue", "resourceAmount", "translate", "advanceResultText", "recordText", "legacyText", "unavailableText", "itemName", "variantName", "abilityNameText", "warriorAbilityName", "conditionDetailText"]);
// Only structural native attributes may bypass presentation validation. Unknown
// attributes are review findings, including future browser/custom extensions.
const structuralAttributes = new Set("popover popoverTarget popoverTargetAction key ref id className htmlFor role type name disabled checked defaultChecked selected multiple required readOnly autoFocus autoComplete tabIndex hidden inert open href target rel download width height rows cols min max step pattern inputMode form method action accept acceptCharset encType colSpan rowSpan scope xmlns viewBox d fill stroke strokeWidth cx cy r x y x1 y1 x2 y2 points transform focusable preserveAspectRatio aria-hidden aria-expanded aria-controls aria-describedby aria-labelledby aria-details aria-errormessage aria-live aria-atomic aria-busy aria-current aria-selected aria-checked aria-disabled aria-required aria-invalid aria-pressed aria-modal aria-haspopup aria-level aria-valuemin aria-valuemax aria-valuenow aria-posinset aria-setsize".split(" "));

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
  // Local bindings are keyed by their checker symbol, so two same-named
  // declarations in different scopes never share an entry and a use site
  // resolves to its own declaration. Without a checker (bare syntactic use of
  // this function) the name is the key, with the old file-wide imprecision.
  const symbolKey = (identifier) => {
    if (!semantic.checker) return identifier.text;
    let symbol = semantic.checker.getSymbolAtLocation(identifier);
    if (symbol && symbol.flags & ts.SymbolFlags.Alias) symbol = semantic.checker.getAliasedSymbol(symbol);
    return symbol ?? identifier.text;
  };
  const declarations = new Map();
  const destructured = new Map();
  const collect = (node) => {
    if (ts.isFunctionDeclaration(node) && node.name && node.body) {
      const key = symbolKey(node.name);
      declarations.set(key, [...(declarations.get(key) ?? []), node]);
    }
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer) {
      const key = symbolKey(node.name);
      const values = declarations.get(key) ?? [];
      values.push(node.initializer);
      declarations.set(key, values);
    }
    if (ts.isVariableDeclaration(node) && ts.isObjectBindingPattern(node.name) && node.initializer) {
      for (const binding of node.name.elements) {
        if (ts.isIdentifier(binding.name)) destructured.set(symbolKey(binding.name), { owner: node.initializer, key: binding.propertyName?.getText(file) ?? binding.name.text, node: binding });
      }
    }
    ts.forEachChild(node, collect);
  };
  collect(file);
  // `presentationOutput` is trusted by its import, not by its name: a local
  // function shadowing the adapter's name must not launder text through it.
  const isOutputAdapter = (identifier) => {
    if (!outputAdapters.has(identifier.text)) return false;
    if (!semantic.checker) return true;
    const symbol = semantic.checker.getSymbolAtLocation(identifier);
    return (symbol?.declarations ?? []).some(ts.isImportSpecifier);
  };
  const indirectWriter = (node, seen = new Set()) => {
    if (!node || seen.has(node)) return false;
    const next = new Set(seen).add(node);
    if (ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) return /^(?:write|writeln|setAttribute|setAttributeNS|append|prepend|replaceChildren|createTextNode|insertAdjacentText|insertAdjacentHTML|fillText|strokeText|drawText|cell|multiCell|alert|confirm|prompt|setHTML|setHTMLUnsafe)$/.test(property(node) ?? "");
    if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "bind") return indirectWriter(node.expression.expression, next);
    if (ts.isIdentifier(node)) {
      if ((declarations.get(symbolKey(node)) ?? []).some((value) => indirectWriter(value, next))) return true;
      const binding = destructured.get(symbolKey(node));
      if (binding && /^(?:write|writeln|setAttribute|append|prepend|createTextNode|fillText|strokeText)$/.test(binding.key)) return true;
    }
    return false;
  };
  // JSX control flow is not itself text. Its leaf outputs are visited below.
  const reactNodeTyped = (type) => type.aliasSymbol?.name === "ReactNode"
    || (type.isUnion() && type.types.some((member) => member.getSymbol()?.name === "ReactElement") && type.types.some((member) => member.flags & ts.TypeFlags.StringLike));
  const validatedOutput = (node) => {
    if (!node) return true;
    if (ts.isIdentifier(node) && node.text === "undefined") return true;
    if (semantic.checker) {
      const structural = (type) => type.isUnion() ? type.types.every(structural) :
        Boolean(type.flags & (ts.TypeFlags.Undefined | ts.TypeFlags.Null | ts.TypeFlags.BooleanLike)) ||
        (type.getSymbol()?.name === "ReactElement" && type.getSymbol().declarations?.some((declaration) => declaration.getSourceFile().fileName.replaceAll("\\", "/").includes("/@types/react/")));
      if (structural(semantic.checker.getTypeAtLocation(node))) return true;
      // A ReactNode-typed binding (children, slot props) forwards content the
      // caller produced; the caller's argument is checked at its own site
      // (see the component-prop branch), so the pass-through is not a source.
      if (reactNodeTyped(semantic.checker.getTypeAtLocation(node)) && (ts.isIdentifier(node) || ts.isPropertyAccessExpression(node))) return true;
    }
    if (ts.isParenthesizedExpression(node)) return validatedOutput(node.expression);
    if (ts.isJsxElement(node) || ts.isJsxFragment(node) || ts.isJsxSelfClosingElement(node)) return true;
    if ([ts.SyntaxKind.NullKeyword, ts.SyntaxKind.FalseKeyword, ts.SyntaxKind.TrueKeyword].includes(node.kind)) return true;
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && isOutputAdapter(node.expression)) return true;
    if (ts.isConditionalExpression(node)) return validatedOutput(node.whenTrue) && validatedOutput(node.whenFalse);
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) return validatedOutput(node.right);
    if (ts.isCallExpression(node)) {
      const called = ts.isParenthesizedExpression(node.expression) ? node.expression.expression : node.expression;
      const callback = ts.isArrowFunction(called) || ts.isFunctionExpression(called) ? called
        : ts.isPropertyAccessExpression(called) && called.name.text === "map" ? node.arguments[0]
        : ts.isPropertyAccessExpression(called) && called.expression.getText(file) === "Array" && called.name.text === "from" ? node.arguments[1]
        : undefined;
      // A callback passed by reference (`rows.map(renderRow)`) is resolved to
      // its local declaration so its returns are judged like an inline arrow.
      // Resolved through the checker's symbol, not by name: several
      // scopes may declare a callback with the same name.
      const bySymbol = (identifier) => {
        let symbol = semantic.checker?.getSymbolAtLocation(identifier);
        if (symbol && symbol.flags & ts.SymbolFlags.Alias) symbol = semantic.checker.getAliasedSymbol(symbol);
        const declaration = symbol?.valueDeclaration;
        if (!declaration) return undefined;
        if (ts.isFunctionDeclaration(declaration)) return declaration;
        return ts.isVariableDeclaration(declaration) ? declaration.initializer : undefined;
      };
      const resolved = callback && ts.isIdentifier(callback) ? bySymbol(callback) : callback;
      if (!resolved || (!ts.isArrowFunction(resolved) && !ts.isFunctionExpression(resolved) && !ts.isFunctionDeclaration(resolved)) || !resolved.body) return false;
      if (!ts.isBlock(resolved.body)) return validatedOutput(resolved.body);
      const returns = [];
      const scan = (child) => { if (ts.isReturnStatement(child)) returns.push(child.expression); else if (!ts.isFunctionLike(child)) ts.forEachChild(child, scan); };
      ts.forEachChild(resolved.body, scan);
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
  const inspectFlow = (node, expression, options) => {
    if (!semantic.trace) return;
    // A value proven safe at the sink (JSX, a branded or adapter-validated
    // value, a map whose callback returns such output) renders only that
    // proven output. The data that selected, keyed or built it never reaches
    // the screen through this sink, so slicing back from it reported every id
    // used to build a list as a "raw origin". Nested sinks inside the JSX are
    // visited and traced on their own.
    if (validatedOutput(expression) || branded(expression)) return;
    const result = semantic.trace(expression, options);
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
  // A type made only of string literals (plus null/undefined) is a closed
  // vocabulary of system values.
  const systemVocabulary = (node) => {
    if (!semantic.checker) return false;
    const type = semantic.checker.getTypeAtLocation(node);
    const members = (type.isUnion() ? type.types : [type]).filter((member) => !(member.flags & (ts.TypeFlags.Undefined | ts.TypeFlags.Null)));
    return members.length > 0 && members.every((member) => member.flags & ts.TypeFlags.StringLiteral);
  };
  const projectComponent = (tagName) => {
    if (!semantic.checker) return false;
    let target = semantic.checker.getSymbolAtLocation(tagName);
    if (target && target.flags & ts.SymbolFlags.Alias) target = semantic.checker.getAliasedSymbol(target);
    const declarations = target?.declarations ?? [];
    return declarations.length > 0 && declarations.every((declaration) => !declaration.getSourceFile().fileName.includes("node_modules"));
  };
  const declaredReactNode = (expression) => {
    const declared = semantic.checker?.getContextualType(expression);
    return Boolean(declared && reactNodeTyped(declared));
  };
  // A custom prop whose resolved type cannot be display text: numbers, booleans,
  // enums, callbacks, and whitespace-free string-literal unions (ids, kinds,
  // locales). Object models are not text either — the component that renders
  // their fields is audited at its own sinks, so flagging the pass-through only
  // duplicated the child's finding. Plain `string`, `any`/`unknown` and arrays
  // of them stay findings.
  const nonTextProp = (node) => {
    if (!semantic.checker) return false;
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return !/\s/.test(node.text);
    const safe = (type) => {
      if (type.isUnionOrIntersection()) return type.types.every(safe);
      if (type.flags & (ts.TypeFlags.NumberLike | ts.TypeFlags.BooleanLike | ts.TypeFlags.Undefined
        | ts.TypeFlags.Null | ts.TypeFlags.EnumLike | ts.TypeFlags.ESSymbolLike | ts.TypeFlags.Never | ts.TypeFlags.Void)) return true;
      if (type.flags & ts.TypeFlags.StringLiteral) return !/\s/.test(type.value);
      if (type.flags & (ts.TypeFlags.StringLike | ts.TypeFlags.Any | ts.TypeFlags.Unknown)) return false;
      if (type.getCallSignatures().length) return true;
      if (semantic.checker.isArrayLikeType(type)) {
        const element = semantic.checker.getElementTypeOfArrayType?.(type) ?? type.getNumberIndexType();
        return element ? safe(element) : true;
      }
      return Boolean(type.flags & ts.TypeFlags.Object);
    };
    return safe(semantic.checker.getTypeAtLocation(node));
  };
  const property = (node) => ts.isPropertyAccessExpression(node) ? node.name.text : ts.isElementAccessExpression(node) && node.argumentExpression && ts.isStringLiteral(node.argumentExpression) ? node.argumentExpression.text : undefined;
  const inspectExpression = (node) => {
    if (ts.isIdentifier(node) && argumentsByParameter.has(symbolKey(node))) {
      const key = symbolKey(node);
      const argument = argumentsByParameter.get(key);
      argumentsByParameter.delete(key);
      inspectExpression(argument);
      argumentsByParameter.set(key, argument);
      return;
    }
    if (ts.isIdentifier(node) && destructured.has(symbolKey(node))) {
      const binding = destructured.get(symbolKey(node));
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
    if (ts.isIdentifier(node) && declarations.has(symbolKey(node)) && !resolving.has(symbolKey(node))) {
      const key = symbolKey(node);
      resolving.add(key);
      declarations.get(key).forEach(inspectExpression);
      resolving.delete(key);
      return;
    }
    if (ts.isCallExpression(node)) {
      // The imported adapter's argument is checked against the opaque union by
      // TypeScript. IDs used to resolve it are not themselves visible values.
      if (ts.isIdentifier(node.expression) && isOutputAdapter(node.expression)) return;
      const name = ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : ts.isIdentifier(node.expression) ? node.expression.text : "";
      const callee = ts.isIdentifier(node.expression) ? symbolKey(node.expression) : undefined;
      const local = callee === undefined ? undefined : declarations.get(callee);
      if (local?.length === 1 && (ts.isArrowFunction(local[0]) || ts.isFunctionDeclaration(local[0])) && !resolving.has(callee)) {
        resolving.add(callee);
        const previousArguments = new Map(argumentsByParameter);
        local[0].parameters.forEach((parameter, index) => {
          if (ts.isIdentifier(parameter.name) && node.arguments[index]) argumentsByParameter.set(symbolKey(parameter.name), node.arguments[index]);
        });
        inspectExpression(local[0]);
        argumentsByParameter.clear();
        previousArguments.forEach((value, key) => argumentsByParameter.set(key, value));
        resolving.delete(callee);
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
      const candidates = ts.isIdentifier(owner) ? declarations.get(symbolKey(owner)) : [owner];
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
    if (ts.isJsxExpression(node) && node.expression && ts.isBinaryExpression(node.expression) && node.expression.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) {
      const left = node.expression.left;
      // React renders a falsy guard verbatim: `0 && x` prints "0" and
      // `NaN && x` prints "NaN", while `"" && x`, false, null and undefined
      // print nothing. Only number-like or untyped guards can therefore leak.
      const unsafeGuard = (type) => type.isUnion() ? type.types.some(unsafeGuard) : Boolean(type.flags & (ts.TypeFlags.NumberLike | ts.TypeFlags.BigIntLike | ts.TypeFlags.Any | ts.TypeFlags.Unknown));
      if (semantic.checker ? unsafeGuard(semantic.checker.getTypeAtLocation(left)) : !ts.isBinaryExpression(left) && ![ts.SyntaxKind.TrueKeyword, ts.SyntaxKind.FalseKeyword].includes(left.kind)) review(node, "conditional-text", left, "unclassified-render-guard");
    }
    if (ts.isJsxSpreadAttribute(node)) {
      // Spread props into a project component are audited where the
      // component renders them, like named props — unless the spread
      // supplies a ReactNode slot, whose content the component renders opaquely.
      const owner = node.parent.parent.tagName;
      const spreadType = semantic.checker?.getTypeAtLocation(node.expression);
      const declared = semantic.checker?.getContextualType(node.expression);
      const fillsSlot = !spreadType || !declared || spreadType.getProperties().some((member) => {
        const target = declared.getProperty(member.name);
        // A prop the component does not declare is never read by it.
        return Boolean(target) && reactNodeTyped(semantic.checker.getTypeOfSymbolAtLocation(target, node.expression));
      });
      if (!/^[a-z][a-z0-9-]*$/.test(owner.getText(file)) && projectComponent(owner) && !fillsSlot) sinks.push({ ...location(node), element: guiLocation(node), kind: "spread-props", classification: "audited-at-component", expression: node.expression.getText(file) });
      else review(node, "spread-props", node.expression, "unclassified-spread");
    }
    if (ts.isJsxAttribute(node) && node.initializer) {
      const tag = node.parent.parent.tagName.getText(file), name = node.name.text;
      const expression = ts.isJsxExpression(node.initializer) ? node.initializer.expression ?? node.initializer : node.initializer;
      const intrinsic = /^[a-z][a-z0-9-]*$/.test(tag);
      if (name === "dangerouslySetInnerHTML") review(node, "html-injection", expression, "unclassified-html");
      else if (name.toLowerCase() === "srcdoc") review(node, "embedded-document", expression, "unclassified-html");
      else if (tag.includes("-") || ["animate", "set", "animateTransform"].includes(tag)) review(node, "dynamic-attribute", expression, "unclassified-element-attribute");
      else if (name === "style") {
        const styleBranches = (value) => ts.isParenthesizedExpression(value) ? styleBranches(value.expression)
          : ts.isConditionalExpression(value) ? [...styleBranches(value.whenTrue), ...styleBranches(value.whenFalse)]
          : ts.isIdentifier(value) && value.text === "undefined" ? []
          : [value];
        const branches = styleBranches(expression);
        if (!branches.every(ts.isObjectLiteralExpression)) review(node, "inline-style", expression, "unclassified-style");
        else for (const prop of branches.flatMap((branch) => branch.properties)) {
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
        else if (node.parent.properties.some((prop) => ts.isJsxAttribute(prop) && ["readOnly", "disabled"].includes(prop.name.text) && (!prop.initializer || prop.initializer.getText(file) !== "{false}"))
          || systemVocabulary(expression)) {
          // A read-only control is a display, not an edit; and a value typed
          // as a string-literal union is system vocabulary (a kind, a
          // status), never free text the user typed. Both must be localized.
          review(node, "control-value", expression, "unclassified-control-value");
        }
        else {
          // An editable text control shows what the user typed (or the
          // user-named record being renamed). It is a finding only when the
          // flow trace shows a raw system origin (an id, a KB field) seeding it.
          sinks.push({ ...location(node), element: tag, kind: "control-value", classification: "user-editable", expression: expression.getText(file) });
          inspectFlow(node, expression, { userAuthored: true });
        }
      } else if (!intrinsic && (!attributes.has(name) || projectComponent(node.parent.parent.tagName)) && !["key", "ref"].includes(name) && !/^on[A-Z]/.test(name)) {
        // Custom props can contain indirect labels, nested row models or callbacks.
        // Their names are not evidence that they are non-visible.
        if (branded(expression) || validatedOutput(expression)) sinks.push({ ...location(node), element: tag, kind: "component-prop", classification: "validated-presentation", expression: expression.getText(file) });
        else if (nonTextProp(expression)) sinks.push({ ...location(node), element: tag, kind: "component-prop", classification: "non-text-type", expression: expression.getText(file) });
        else if (projectComponent(node.parent.parent.tagName) && !declaredReactNode(expression)) {
          // The component is analysed here too: every place it renders this
          // prop is one of its own sinks, so a raw value is reported there
          // (unvalidated-output / raw-text-flow). Only a ReactNode-declared
          // slot renders the caller's value opaquely and stays checked here.
          sinks.push({ ...location(node), element: tag, kind: "component-prop", classification: "audited-at-component", expression: expression.getText(file) });
        }
        else review(node, "component-prop", expression, "unclassified-component-prop");
      } else if (intrinsic && name === "children") record(node, "children-prop", expression);
      else if (intrinsic && name.startsWith("data-") && !attributes.has(name)) {
        // Not a visible attribute: the CSS audit only lets `content: attr()`
        // expose the visible ones, and JS that reads the dataset back is
        // traced at the sink where it renders.
        sinks.push({ ...location(node), element: tag, kind: "custom-data", classification: "non-display-attribute", expression: expression.getText(file) });
      }
      else if (intrinsic && !attributes.has(name) && !structuralAttributes.has(name) && !/^on[A-Z]/.test(name)) review(node, "native-attribute", expression, "unclassified-native-attribute");
    }
    if (ts.isCallExpression(node)) {
      const name = ts.isPropertyAccessExpression(node.expression) ? node.expression.name.text : node.expression.getText(file);
      if (["createElement", "cloneElement", "jsx", "jsxs", "jsxDEV"].includes(name)) {
        // Native createElement only creates an empty node; subsequent writes are audited.
        const native = ts.isPropertyAccessExpression(node.expression) && /(?:^|\.)document$/.test(node.expression.expression.getText(file)) && name === "createElement";
        // A context provider renders its children unchanged; its `value`
        // is data for consumers, whose own sinks are audited.
        const provider = name === "createElement" && node.arguments[0] && ts.isPropertyAccessExpression(node.arguments[0]) && node.arguments[0].name.text === "Provider";
        if (!native && !provider) review(node, "dynamic-element", node, "unclassified-dynamic-element");
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
      // The localization engine's own table dispatch
      // (`parameterMessages[key][locale](args)`) is the owned UiText
      // constructor resolving its reviewed message table, not an open call.
      if (ts.isElementAccessExpression(node.expression) && filename.replaceAll("\\", "/") !== "src/features/campaign/i18n-core.ts") review(node, "dynamic-call", node, "unclassified-computed-call");
      if (["eval", "Function", "importScripts"].includes(name)) review(node, "dynamic-code", node, "unclassified-dynamic-code");
      if (["render", "createPortal"].includes(name) && node.arguments[0]) record(node, "react-root", node.arguments[0]);
      if (node.expression.kind === ts.SyntaxKind.ImportKeyword && (!ts.isStringLiteral(node.arguments[0]) || !node.arguments[0].text.startsWith("."))) review(node, "dynamic-import", node, "unclassified-dynamic-code");
    }
    if (ts.isNewExpression(node) && ["Function", "Worker", "SharedWorker"].includes(node.expression.getText(file))) review(node, "dynamic-code", node, "unclassified-dynamic-code");
    if (ts.isBinaryExpression(node) && [ts.SyntaxKind.EqualsToken, ts.SyntaxKind.PlusEqualsToken].includes(node.operatorToken.kind)) {
      const name = property(node.left);
      if ((ts.isPropertyAccessExpression(node.left) || ts.isElementAccessExpression(node.left)) && ["style"].includes(property(node.left.expression))) review(node, "indirect-dom-property", node.right, "unclassified-property-write");
      // A computed write is a GUI concern only when its receiver is a DOM
      // object (element, style, dataset, attribute map) or untyped. Writes
      // into plain records (`out[key] = text`) build data that reaches the
      // screen only through sinks audited on their own.
      const domReceiver = (receiver) => {
        if (!semantic.checker) return true;
        const type = semantic.checker.getTypeAtLocation(receiver);
        if (type.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown)) return true;
        const name = semantic.checker.typeToString(type);
        return /\b(?:HTML\w*Element|Element|Node|CSSStyleDeclaration|DOMStringMap|NamedNodeMap|Document|Window)\b/.test(name);
      };
      if (ts.isElementAccessExpression(node.left) && !ts.isStringLiteral(node.left.argumentExpression) && domReceiver(node.left.expression)) review(node, "dynamic-write", node, "unclassified-computed-write");
      else if (["value", "defaultValue", "placeholder", "alt", "ariaLabel", "outerHTML", "nodeValue", "data"].includes(name)) {
        const cleared = ts.isStringLiteral(node.right) && node.right.text === "";
        if (cleared || validatedOutput(node.right) || branded(node.right)) sinks.push({ ...location(node), kind: "dom-property", classification: cleared ? "cleared" : "validated-presentation", expression: node.right.getText(file) });
        else review(node, "dom-property", node.right, "unclassified-property-write");
      }
      else if (node.operatorToken.kind === ts.SyntaxKind.PlusEqualsToken && ["textContent", "innerText", "innerHTML", "outerHTML", "title"].includes(name)) record(node, "dom-write", node.right);
      if (ts.isPropertyAccessExpression(node.left) && ts.isPropertyAccessExpression(node.left.expression) && node.left.expression.name.text === "style" && ["content", "cssText"].includes(name)) review(node, "dynamic-css", node.right, "unclassified-style-content");
    }
    if (ts.isAsExpression(node) && node.type.kind === ts.SyntaxKind.AnyKeyword) {
      findings.push({ ...location(node), reason: "presentation-cast", expression: node.getText(file) });
    }
    if (ts.isAsExpression(node) && /\b(?:UiText|LocalizedText|PresentationText|ResolvedKbText|FormattedText|EnumText|CatalogueText)\b/.test(node.type.getText(file))) {
      const normalized = filename.replaceAll("\\", "/");
      const ownedUiConstructor = normalized === "src/features/campaign/i18n-core.ts" && node.type.getText(file) === "UiText";
      const ownedValueConstructor = normalized === "src/features/campaign/presentation-values.ts" && node.type.getText(file) === "FormattedText";
      const ownedEnumConstructor = normalized === "src/features/campaign/presentation-enums.ts" && node.type.getText(file) === "EnumText";
      // The packages/typescript text adapters are reviewed constructor modules
      // (see the allowlist in presentation-type-audit.mjs).
      const ownedKbConstructor = normalized.endsWith("packages/typescript/adapters/knowledge-reader/presentation.ts") && node.type.getText(file) === "ResolvedKbText";
      const ownedCatalogueConstructor = normalized.endsWith("packages/typescript/application/rules/catalogue-text.ts") && node.type.getText(file) === "CatalogueText";
      if (!ownedUiConstructor && !ownedValueConstructor && !ownedEnumConstructor && !ownedKbConstructor && !ownedCatalogueConstructor) findings.push({ ...location(node), reason: "presentation-cast", expression: node.getText(file) });
    }
    if (ts.isJsxText(node) && node.text.trim()) record(node, "jsx-text");
    if (ts.isJsxExpression(node) && node.expression && !ts.isJsxAttribute(node.parent)) record(node, "jsx-expression", node.expression);
    // Visible attribute names (title, label, placeholder…) are text sinks on
    // intrinsic elements and on third-party components. On a project component
    // they are ordinary props, classified by the component-prop branch: the
    // component's own sinks audit how it renders them.
    if (ts.isJsxAttribute(node) && attributes.has(node.name.text) && node.initializer
        && (/^[a-z][a-z0-9-]*$/.test(node.parent.parent.tagName.getText(file)) || !projectComponent(node.parent.parent.tagName))) record(node, "attribute", ts.isJsxExpression(node.initializer) ? node.initializer.expression ?? node.initializer : node.initializer);
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

/**
 * The HTML shell is shown before React mounts. Its `<html lang>` and `<title>`
 * are acceptable pre-hydration defaults only when the app keeps them in sync
 * with the active locale at runtime (writes to `documentElement.lang` and
 * `document.title`); any other static text or visible attribute is a finding.
 */
export function inspectHtmlDocument(source, filename, program) {
  const sinks = [], findings = [];
  const lineOf = (index) => source.slice(0, index).split("\n").length;
  const writes = { lang: false, title: false };
  for (const file of program?.getSourceFiles() ?? []) {
    if (file.isDeclarationFile || file.fileName.includes("node_modules") || /\.test\./.test(file.fileName)) continue;
    if (/documentElement\.lang\s*=/.test(file.text)) writes.lang = true;
    if (/document\.title\s*=/.test(file.text)) writes.title = true;
  }
  const lang = /<html\b[^>]*\blang\s*=\s*["']([^"']*)["']/i.exec(source);
  if (lang) {
    sinks.push({ file: filename, line: lineOf(lang.index), kind: "document-language", expression: lang[1] });
    if (!writes.lang) findings.push({ file: filename, line: lineOf(lang.index), kind: "document-language", reason: "static-document-language", expression: lang[0] });
  } else findings.push({ file: filename, line: 1, kind: "document-language", reason: "missing-document-language", expression: "<html>" });
  const title = /<title>([\s\S]*?)<\/title>/i.exec(source);
  if (title) {
    sinks.push({ file: filename, line: lineOf(title.index), kind: "document-title", expression: title[1].trim() });
    if (!writes.title && title[1].trim()) findings.push({ file: filename, line: lineOf(title.index), kind: "document-title", reason: "static-document-title", expression: title[0] });
  }
  // Any other text node or visible attribute in the shell is static, unlocalized text.
  const body = source.replace(/<title>[\s\S]*?<\/title>/gi, "").replace(/<(script|style)\b[\s\S]*?<\/\1>/gi, "").replace(/<!--[\s\S]*?-->/g, "");
  for (const match of body.matchAll(/>([^<]+)</g)) {
    const text = match[1].trim();
    if (text) findings.push({ file: filename, line: lineOf(source.indexOf(match[1])), kind: "document-text", reason: "static-document-text", expression: text });
  }
  for (const match of body.matchAll(/\s(title|alt|placeholder|aria-label)\s*=\s*["']([^"']+)["']/gi)) {
    findings.push({ file: filename, line: lineOf(source.indexOf(match[0])), kind: "document-attribute", reason: "static-document-text", expression: match[0].trim() });
  }
  return { sinks, findings };
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

function files(path) {
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) => entry.isDirectory() ? files(resolve(path, entry.name)) : /\.(?:[cm]?[jt]sx?|css|html|svg)$/.test(entry.name) && !/\.test\./.test(entry.name) && entry.name !== "test-setup.ts" ? [resolve(path, entry.name)] : []);
}

/** The complete audit: every GUI source, with types and the full flow trace. */
export function audit(root) {
  const sinks = [], findings = [];
  const program = createPresentationProgram(root), checker = program.getTypeChecker();
  const trace = createPresentationFlowAudit(program, root, { maxSteps: 2500, maxDepth: 80 });
  const paths = files(resolve(root, "src"));
  paths.push(resolve(root, "index.html"));
  // Imported workspace modules may render text without living under src/.
  // Imported JSON is data the TS/JSX analyzer reads through typed modules,
  // not a GUI source: its values reach a sink only through code audited here.
  for (const file of program.getSourceFiles()) if (!file.isDeclarationFile && !file.fileName.includes("node_modules") && !/\.test\./.test(file.fileName) && !file.fileName.endsWith("test-setup.ts") && !file.fileName.endsWith(".json")) paths.push(file.fileName);
  if (existsSync(resolve(root, "public"))) paths.push(...files(resolve(root, "public")));
  for (const path of new Set(paths.map((path) => resolve(path)))) {
    const name = relative(root, path).replaceAll("\\", "/");
    const source = readFileSync(path, "utf8");
    if (path.endsWith(".html")) {
      const result = inspectHtmlDocument(source, name, program);
      sinks.push(...result.sinks); findings.push(...result.findings);
      continue;
    }
    if (!/\.(tsx?|css)$/.test(path)) {
      const entry = { file: name, line: 1, kind: "unclassified-source", expression: "Revisar esta fuente de GUI: no está cubierta por el analizador TypeScript/JSX/CSS." };
      sinks.push(entry); findings.push({ ...entry, reason: "unclassified-source-format" });
      continue;
    }
    if (path.endsWith(".css")) {
      const result = inspectCssPresentation(source, name);
      sinks.push(...result.sinks); findings.push(...result.findings);
      continue;
    }
    const result = inspectPresentation(source, name, { file: program.getSourceFile(path), checker, trace });
    sinks.push(...result.sinks); findings.push(...result.findings);
  }
  findings.push(...auditPresentationTypes(root, program));
  for (const diagnostic of ts.getPreEmitDiagnostics(program)) {
    findings.push({ file: diagnostic.file ? relative(root, diagnostic.file.fileName).replaceAll("\\", "/") : "tsconfig.json", line: diagnostic.file && diagnostic.start !== undefined ? diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start).line + 1 : 1, reason: "compiler-error", expression: ts.flattenDiagnosticMessageText(diagnostic.messageText, " ") });
  }
  return { sinks, findings };
}

/**
 * Audit one in-memory source file inside the app's real type environment —
 * the regression corpus of the audit itself. The fixture is served by a
 * compiler host at `virtualPath` (inside the app, so its imports resolve)
 * and is never written to disk. Returns the fixture's findings only.
 */
export function auditVirtualFile(root, virtualPath, source) {
  const config = ts.readConfigFile(resolve(root, "tsconfig.json"), ts.sys.readFile);
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, root);
  const fullPath = resolve(root, virtualPath);
  const host = ts.createCompilerHost(parsed.options, true);
  const readFile = host.readFile.bind(host), fileExists = host.fileExists.bind(host), getSourceFile = host.getSourceFile.bind(host);
  host.readFile = (name) => resolve(name) === fullPath ? source : readFile(name);
  host.fileExists = (name) => resolve(name) === fullPath || fileExists(name);
  host.getSourceFile = (name, language, ...rest) => resolve(name) === fullPath ? ts.createSourceFile(name, source, language, true, ts.ScriptKind.TSX) : getSourceFile(name, language, ...rest);
  const program = ts.createProgram([...parsed.fileNames, fullPath], parsed.options, host);
  const checker = program.getTypeChecker();
  const trace = createPresentationFlowAudit(program, root, { maxSteps: 2500, maxDepth: 80 });
  const file = program.getSourceFile(fullPath);
  const name = relative(root, fullPath).replaceAll("\\", "/");
  const findings = inspectPresentation(source, name, { file, checker, trace }).findings;
  findings.push(...inspectPresentationTypes(program, file, root));
  for (const diagnostic of ts.getPreEmitDiagnostics(program, file)) {
    findings.push({ file: name, line: diagnostic.start === undefined ? 1 : file.getLineAndCharacterOfPosition(diagnostic.start).line + 1, reason: "compiler-error", expression: ts.flattenDiagnosticMessageText(diagnostic.messageText, " ") });
  }
  return findings;
}

export function guiReport(result) {
  const cell = (value) => String(value ?? "—").replaceAll("|", "\\|").replace(/\r?\n/g, " ").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  const counts = new Map();
  for (const row of result.findings) counts.set(row.reason, (counts.get(row.reason) ?? 0) + 1);
  return ["# Auditoría de textos de la GUI", "", `${result.sinks.length} puntos inventariados; ${result.findings.length} incidencias o salidas sin clasificar.`, "", "Una salida sin clasificar no es una fuga confirmada: el analizador no puede demostrar su protección. Revisar origen y destino antes de corregirla. No ocultar incidencias mediante casts o supresiones.", "", "## Resumen", "", ...[...counts].map(([reason, count]) => `- ${reason}: ${count}`), "", "## Ubicaciones", "", "| Archivo | Línea | Elemento | Motivo | Expresión | Origen y recorrido |", "| --- | --- | --- | --- | --- | --- |", ...result.findings.map((row) => `| ${cell(row.file)} | ${row.line} | ${cell(row.element)} | ${cell(row.reason)} | ${cell(row.expression)} | ${cell(row.origins ? row.origins.map((origin) => `${origin.file}:${origin.line} (${origin.expression}) via ${origin.path.map((step) => `${step.file}:${step.line}`).join(" → ")}`).join("; ") + (row.truncated ? " [recorrido truncado: no enumera todos los orígenes]" : "") : undefined)} |`), "", "Alcance: código web TypeScript/JSX/CSS analizado y tipos del proyecto. No prueba calidad lingüística, estados ejecutados, bibliotecas externas, HTML externo ni cualquier construcción dinámica de JavaScript. Los adaptadores autorizados siguen requiriendo revisión y pruebas.", ""].join("\n");
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  // The tool lives in tools/web; the surface it audits is the web application.
  const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
  const root = resolve(repoRoot, "apps", "warband-manager-web");
  const result = audit(root);
  const output = resolve(repoRoot, "outputs/web-presentation/gui-text-audit.json");
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
  writeFileSync(output.replace(/\.json$/, ".md"), guiReport(result));
  console.log(`${result.sinks.length} presentation sinks; ${result.findings.length} findings requiring review. ${output}`);
  console.log(`Readable report: ${output.replace(/\.json$/, ".md")}`);
  for (const finding of result.findings.slice(0, 20)) console.log(`  finding: ${finding.file}:${finding.line} ${finding.reason} | ${String(finding.expression ?? "").replace(/\s+/g, " ").slice(0, 120)}`);
  if (process.argv.includes("--check") && result.findings.length) process.exitCode = 1;
}
