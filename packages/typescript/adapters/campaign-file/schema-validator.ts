/**
 * P3.2: minimal JSON Schema (draft 2020-12) validator covering exactly the
 * keyword subset the v4 contract schema uses — no third-party dependency in
 * the browser bundle. Errors carry the schema's JSON path, mirroring the
 * Python reader's reporting (e.g. `campaign.warriors[3].stats`).
 *
 * Supported keywords: type (incl. union forms), const, enum, required,
 * properties, additionalProperties (false | schema), items (schema | false),
 * prefixItems, minItems/maxItems, minLength, minimum, pattern, $ref
 * (local `#/$defs/...`), $defs.
 *
 * Not supported (unused by the contract): remote refs, oneOf/anyOf, allOf,
 * not, dependencies, format. If the contract ever needs them, extend here —
 * or switch the embed to a compiled validator at build time.
 */

export interface SchemaError {
  /** JSON path inside the validated document, e.g. `campaign.warriors[3]`. */
  readonly location: string;
  /** Human-readable description of the violation. */
  readonly message: string;
}

type Schema = Record<string, unknown>;

const ROOT = "#";

function resolveRef(root: Schema, ref: string): Schema {
  if (!ref.startsWith(ROOT)) {
    throw new Error(`Unsupported $ref in v4 schema: ${ref}`);
  }
  let node: unknown = root;
  for (const part of ref.slice(ROOT.length).split("/").filter(Boolean)) {
    if (typeof node !== "object" || node === null) {
      throw new Error(`Unresolvable $ref in v4 schema: ${ref}`);
    }
    node = (node as Schema)[part.replace(/~1/g, "/").replace(/~0/g, "~")];
  }
  if (typeof node !== "object" || node === null) {
    throw new Error(`Unresolvable $ref in v4 schema: ${ref}`);
  }
  return node as Schema;
}

function isInteger(value: number): boolean {
  return Number.isInteger(value);
}

function typeMatches(value: unknown, type: string): boolean {
  switch (type) {
    case "object":
      return typeof value === "object" && value !== null && !Array.isArray(value);
    case "array":
      return Array.isArray(value);
    case "string":
      return typeof value === "string";
    case "integer":
      return typeof value === "number" && isInteger(value);
    case "number":
      return typeof value === "number";
    case "boolean":
      return typeof value === "boolean";
    case "null":
      return value === null;
    default:
      return false;
  }
}

function checkType(value: unknown, type: unknown, location: string, errors: SchemaError[]): void {
  if (typeof type === "string") {
    if (!typeMatches(value, type)) {
      errors.push({ location, message: `${location}: expected ${type}` });
    }
    return;
  }
  if (Array.isArray(type)) {
    if (!type.some((t) => typeof t === "string" && typeMatches(value, t))) {
      errors.push({ location, message: `${location}: expected one of ${type.join(" | ")}` });
    }
  }
}

function validate(
  root: Schema,
  schema: Schema,
  value: unknown,
  location: string,
  errors: SchemaError[],
): void {
  // Resolve local refs first; a ref replaces the schema entirely.
  const ref = schema["$ref"];
  if (typeof ref === "string") {
    validate(root, resolveRef(root, ref), value, location, errors);
    return;
  }

  const types = schema["type"];
  if (types !== undefined) {
    checkType(value, types, location, errors);
    if (errors.length > 0 && errors[errors.length - 1].location === location) {
      // A type mismatch makes deeper checks meaningless for this node.
      return;
    }
  }

  const constant = schema["const"];
  if (constant !== undefined && JSON.stringify(value) !== JSON.stringify(constant)) {
    errors.push({ location, message: `${location}: must equal ${JSON.stringify(constant)}` });
  }

  const pattern = schema["pattern"];
  if (typeof pattern === "string" && typeof value === "string") {
    if (!new RegExp(pattern).test(value)) {
      errors.push({ location, message: `${location}: does not match required pattern` });
    }
  }

  const minLength = schema["minLength"];
  if (typeof minLength === "number" && typeof value === "string" && value.length < minLength) {
    errors.push({ location, message: `${location}: must not be empty` });
  }

  const minimum = schema["minimum"];
  if (typeof minimum === "number" && typeof value === "number" && value < minimum) {
    errors.push({ location, message: `${location}: must be >= ${minimum}` });
  }

  const enumeration = schema["enum"];
  if (Array.isArray(enumeration)) {
    const matches = enumeration.some(
      (allowed) => JSON.stringify(allowed) === JSON.stringify(value),
    );
    if (!matches) {
      errors.push({
        location,
        message: `${location}: must be one of ${enumeration.map((v) => JSON.stringify(v)).join(" | ")}`,
      });
    }
  }

  if (typeof value !== "object" || value === null) {
    return;
  }

  if (Array.isArray(value)) {
    const prefixItems = schema["prefixItems"];
    if (Array.isArray(prefixItems)) {
      const limit = Math.min(prefixItems.length, value.length);
      for (let i = 0; i < limit; i++) {
        validate(root, prefixItems[i] as Schema, value[i], `${location}[${i}]`, errors);
      }
    }
    const items = schema["items"];
    if (items === false) {
      if (value.length > (Array.isArray(prefixItems) ? prefixItems.length : 0)) {
        errors.push({
          location,
          message: `${location}: unexpected extra items beyond the fixed tuple`,
        });
      }
    } else if (typeof items === "object" && items !== null) {
      const start = Array.isArray(prefixItems) ? prefixItems.length : 0;
      for (let i = start; i < value.length; i++) {
        validate(root, items as Schema, value[i], `${location}[${i}]`, errors);
      }
    }
    const minItems = schema["minItems"];
    if (typeof minItems === "number" && value.length < minItems) {
      errors.push({ location, message: `${location}: must have at least ${minItems} items` });
    }
    const maxItems = schema["maxItems"];
    if (typeof maxItems === "number" && value.length > maxItems) {
      errors.push({ location, message: `${location}: must have at most ${maxItems} items` });
    }
    return;
  }

  // Object keywords.
  const record = value as Record<string, unknown>;
  const required = schema["required"];
  if (Array.isArray(required)) {
    for (const key of required) {
      if (typeof key === "string" && !(key in record)) {
        errors.push({ location, message: `${location}: missing required property "${key}"` });
      }
    }
  }
  const properties = schema["properties"];
  if (typeof properties === "object" && properties !== null) {
    for (const [key, subschema] of Object.entries(properties as Schema)) {
      if (key in record) {
        validate(
          root,
          subschema as Schema,
          record[key],
          location === "" ? key : `${location}.${key}`,
          errors,
        );
      }
    }
  }
  const additional = schema["additionalProperties"];
  const constrainedExtra =
    additional === false || (typeof additional === "object" && additional !== null);
  if (constrainedExtra) {
    const props =
      typeof properties === "object" && properties !== null
        ? (properties as Schema)
        : {};
    for (const key of Object.keys(record)) {
      if (key in props) {
        continue;
      }
      const path = location === "" ? key : `${location}.${key}`;
      if (additional === false) {
        errors.push({ location: path, message: `${location}: unknown property "${key}"` });
      } else {
        validate(root, additional as Schema, record[key], path, errors);
      }
    }
  }
}

/**
 * Validate `value` against `schema`. Returns all violations (typically one).
 * An empty array means the value conforms.
 */
export function validateAgainstSchema(schema: unknown, value: unknown): SchemaError[] {
  if (typeof schema !== "object" || schema === null) {
    throw new Error("The v4 schema must be an object");
  }
  const errors: SchemaError[] = [];
  validate(schema as Schema, schema as Schema, value, "", errors);
  return errors;
}
