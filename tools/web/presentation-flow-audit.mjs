import ts from "typescript";
import { relative } from "node:path";

const rawFields = /^(?:id|\w+_id|tags?|names?|name_i18n|description|effect|text|label|result|notes?|message|profile_name|applied_label|roll_history)$/;
const brand = /__(?:@)?(?:uiTextBrand|formattedTextBrand|enumTextBrand|resolvedTextBrand|catalogueTextBrand)\b/;
// These nodes reshape the type of a value, never its runtime content. Tracing
// them is required (a cast must not launder raw text) but charging them the work
// budget made ordinary code truncate before reaching its data.
const reshapesTypeOnly = (node) => ts.isAsExpression(node) || ts.isTypeAssertionExpression(node) || ts.isParenthesizedExpression(node) || ts.isNonNullExpression(node);

/** Conservative backwards slice: findings are provenance candidates, not language detection. */
export function createPresentationFlowAudit(program, root, { maxSteps = 250, maxDepth = 24 } = {}) {
  const checker = program.getTypeChecker();
  const writes = new Map(), stateValues = new Map(), collectionWrites = new Map();
  const symbol = (node) => {
    const found = checker.getSymbolAtLocation(node);
    return found?.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(found) : found;
  };
  const add = (map, key, value) => { if (key) map.set(key, [...(map.get(key) ?? []), value]); };
  const ownerSymbol = (node, seen = new Set()) => {
    const key = symbol(node);
    if (!key || seen.has(key)) return key;
    seen.add(key);
    const declaration = key.declarations?.find(ts.isVariableDeclaration);
    return declaration?.initializer && ts.isIdentifier(declaration.initializer) ? ownerSymbol(declaration.initializer, seen) : key;
  };
  const collectionKey = (node) => node && (ts.isStringLiteral(node) || ts.isNumericLiteral(node)) ? node.text : null;
  const files = program.getSourceFiles().filter((file) => !file.isDeclarationFile && !file.fileName.includes("node_modules") && !/\.test\./.test(file.fileName));
  for (const file of files) {
    const scan = (node) => {
      if (ts.isBinaryExpression(node) && [ts.SyntaxKind.EqualsToken, ts.SyntaxKind.PlusEqualsToken].includes(node.operatorToken.kind)) add(writes, symbol(node.left), node.right);
      if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
        const { expression: receiver, name } = node.expression;
        if (ts.isIdentifier(receiver) && receiver.text === "Object" && name.text === "assign" && node.arguments[0]) {
          for (const source of node.arguments.slice(1)) if (ts.isObjectLiteralExpression(source)) for (const property of source.properties) {
            if (ts.isPropertyAssignment(property)) add(collectionWrites, ownerSymbol(node.arguments[0]), { field: property.name.getText().replace(/^['"]|['"]$/g, ""), value: property.initializer });
          }
        } else if (ts.isIdentifier(receiver) && receiver.text === "Reflect" && name.text === "set" && node.arguments[0] && node.arguments[1] && node.arguments[2]) {
          add(collectionWrites, ownerSymbol(node.arguments[0]), { field: collectionKey(node.arguments[1]), value: node.arguments[2] });
        } else if (name.text === "push" || name.text === "set") {
          for (const value of name.text === "push" ? node.arguments : node.arguments.slice(1)) add(collectionWrites, ownerSymbol(receiver), { field: name.text === "set" ? collectionKey(node.arguments[0]) : null, value });
        }
      }
      if (ts.isVariableDeclaration(node) && ts.isArrayBindingPattern(node.name) && node.initializer && ts.isCallExpression(node.initializer) && (/(?:^|\.)useState$/.test(node.initializer.expression.getText(file)) || symbol(node.initializer.expression)?.name === "useState")) {
        const [value, setter] = node.name.elements;
        if (value && setter && ts.isBindingElement(value) && ts.isBindingElement(setter)) {
          const key = symbol(value.name);
          if (node.initializer.arguments[0]) add(writes, key, node.initializer.arguments[0]);
          stateValues.set(symbol(setter.name), key);
        }
      }
      ts.forEachChild(node, scan);
    };
    scan(file);
  }
  for (const file of files) {
    const scan = (node) => {
      if (ts.isCallExpression(node) && stateValues.has(symbol(node.expression))) for (const arg of node.arguments) add(writes, stateValues.get(symbol(node.expression)), arg);
      ts.forEachChild(node, scan);
    };
    scan(file);
  }
  const location = (node) => ({ file: relative(root, node.getSourceFile().fileName).replaceAll("\\", "/"), line: node.getSourceFile().getLineAndCharacterOfPosition(node.getStart()).line + 1, expression: node.getText().slice(0, 240) });
  const opaque = (node) => {
    const safe = (type) => type.isUnion() ? type.types.every(safe) : checker.getPropertiesOfType(type).some((prop) => brand.test(prop.name));
    return safe(checker.getTypeAtLocation(node));
  };
  return (start) => {
    const origins = new Map();
    let budget = maxSteps, truncated = false;
    const incomplete = [];
    const walk = (node, bindings = new Map(), active = new Set(), path = [], charge = true) => {
      if (!node || active.has(node)) return;
      // Type-only nodes describe values; they can never carry text to a sink, so
      // they are neither traversed nor charged. Annotations used to consume the
      // budget of whole sinks before their data was reached.
      if (ts.isTypeNode(node) || ts.isTypeParameterDeclaration(node) || ts.isTypeAliasDeclaration(node)) return;
      if (charge && (--budget < 0 || path.length > maxDepth)) {
        truncated = true;
        if (incomplete.length < 5) incomplete.push({ ...location(node), reason: budget < 0 ? "step-limit" : "depth-limit", path });
        return;
      }
      const next = new Set(active).add(node);
      const step = [...path, location(node)];
      // Fully transparent: a cast is not a data hop, so it neither charges the
      // budget nor lengthens the reported path. The value below it is still traced.
      if (reshapesTypeOnly(node)) { walk(node.expression, bindings, next, path, false); return; }
      if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "bind") {
        walk(node.expression.expression, bindings, next, step);
        for (const argument of node.arguments) walk(argument, bindings, next, step);
        return;
      }
      // Actual typed resolver/formatter output ends the raw-data path. Casts do not.
      if (opaque(node)) return;
      if (ts.isIdentifier(node)) {
        const key = symbol(node);
        if (bindings.has(key)) { walk(bindings.get(key), bindings, next, step); return; }
        for (const value of writes.get(key) ?? []) walk(value, bindings, next, step);
        for (const declaration of key?.declarations ?? []) {
          if (ts.isVariableDeclaration(declaration) || ts.isPropertyAssignment(declaration)) walk(declaration.initializer, bindings, next, step);
          if (ts.isFunctionDeclaration(declaration)) walk(declaration.body, bindings, next, step);
          if (ts.isBindingElement(declaration)) {
            const owner = declaration.parent.parent;
            const field = declaration.propertyName?.getText() ?? declaration.name.getText();
            if (rawFields.test(field) && ts.isObjectBindingPattern(declaration.parent)) origins.set(JSON.stringify(location(declaration)), { ...location(declaration), path: step });
            if (ts.isVariableDeclaration(owner)) walk(owner.initializer, bindings, next, step);
          }
        }
        return;
      }
      if (ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) {
        const field = ts.isPropertyAccessExpression(node) ? node.name.text : node.argumentExpression && ts.isStringLiteral(node.argumentExpression) ? node.argumentExpression.text : "";
        const type = checker.getTypeAtLocation(node);
        if (rawFields.test(field) && !(type.flags & (ts.TypeFlags.NumberLike | ts.TypeFlags.BooleanLike))) origins.set(JSON.stringify(location(node)), { ...location(node), path: step });
        for (const value of writes.get(symbol(node)) ?? []) walk(value, bindings, next, step);
        const owner = node.expression;
        for (const entry of collectionWrites.get(ownerSymbol(owner)) ?? []) if (entry.field === null || entry.field === field) walk(entry.value, bindings, next, step);
        // Follow aliases to object literals and imported property initializers.
        for (const declaration of symbol(ts.isPropertyAccessExpression(node) ? node.name : node)?.declarations ?? []) if (ts.isPropertyAssignment(declaration)) walk(declaration.initializer, bindings, next, step);
        walk(owner, bindings, next, step);
        return;
      }
      if (ts.isCallExpression(node)) {
        if (ts.isIdentifier(node.expression)) for (const declaration of symbol(node.expression)?.declarations ?? []) {
          const bound = ts.isVariableDeclaration(declaration) && declaration.initializer;
          if (bound && ts.isCallExpression(bound) && ts.isPropertyAccessExpression(bound.expression) && bound.expression.name.text === "bind") {
            const targets = ts.isIdentifier(bound.expression.expression) ? node.getSourceFile().statements.filter((statement) => ts.isFunctionDeclaration(statement) && statement.name?.text === bound.expression.expression.text) : [];
            for (const target of targets) if (target.body) {
              const returns = (child) => { if (ts.isReturnStatement(child)) walk(child.expression, bindings, next, step); else if (!ts.isFunctionLike(child)) ts.forEachChild(child, returns); };
              ts.forEachChild(target.body, returns);
            }
          }
        }
        if (ts.isIdentifier(node.expression)) walk(node.expression, bindings, next, step);
        if (ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "get") {
          const key = collectionKey(node.arguments[0]);
          for (const entry of collectionWrites.get(ownerSymbol(node.expression.expression)) ?? []) if (key === null || entry.field === null || entry.field === key) walk(entry.value, bindings, next, step);
        }
        if (ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "join") {
          for (const entry of collectionWrites.get(ownerSymbol(node.expression.expression)) ?? []) if (entry.field === null) walk(entry.value, bindings, next, step);
        }
        const declaration = checker.getResolvedSignature(node)?.declaration;
        if (declaration?.body && !declaration.getSourceFile().fileName.includes("node_modules")) {
          const args = new Map(bindings);
          declaration.parameters.forEach((parameter, index) => { if (node.arguments[index]) args.set(symbol(parameter.name), node.arguments[index]); });
          if (!ts.isBlock(declaration.body)) walk(declaration.body, args, next, step);
          else {
            const returns = (child) => { if (ts.isReturnStatement(child)) walk(child.expression, args, next, step); else if (!ts.isFunctionLike(child)) ts.forEachChild(child, returns); };
            ts.forEachChild(declaration.body, returns);
          }
        }
        // Unknown transforms are not sanitizers: case conversion, join, fallback, etc.
        if (ts.isPropertyAccessExpression(node.expression)) walk(node.expression.expression, bindings, next, step);
        for (const argument of node.arguments) walk(argument, bindings, next, step);
        return;
      }
      if (ts.isConditionalExpression(node)) { walk(node.whenTrue, bindings, next, step); walk(node.whenFalse, bindings, next, step); return; }
      if (ts.isArrowFunction(node) || ts.isFunctionExpression(node)) { walk(node.body, bindings, next, step); return; }
      if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) || ts.isJsxFragment(node)) return;
      ts.forEachChild(node, (child) => walk(child, bindings, next, step));
    };
    walk(start);
    return { origins: [...origins.values()], truncated, incomplete };
  };
}
