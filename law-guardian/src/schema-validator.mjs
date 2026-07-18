function typeMatches(value, type) {
  if (type === 'null') return value === null;
  if (type === 'array') return Array.isArray(value);
  if (type === 'object') return value !== null && typeof value === 'object' && !Array.isArray(value);
  if (type === 'integer') return Number.isInteger(value);
  if (type === 'number') return typeof value === 'number' && Number.isFinite(value);
  return typeof value === type;
}

function addError(errors, path, message) {
  errors.push({ path: path || '$', message });
}

function validateNode(value, schema, path, errors) {
  if (!schema || typeof schema !== 'object') return;
  if ('const' in schema && value !== schema.const) addError(errors, path, `must equal ${JSON.stringify(schema.const)}`);
  if (schema.enum && !schema.enum.includes(value)) addError(errors, path, `must be one of ${schema.enum.join(', ')}`);

  const allowedTypes = Array.isArray(schema.type) ? schema.type : schema.type ? [schema.type] : [];
  if (allowedTypes.length && !allowedTypes.some((type) => typeMatches(value, type))) {
    addError(errors, path, `must be of type ${allowedTypes.join(' or ')}`);
    return;
  }
  if (value === null) return;

  if (typeof value === 'string') {
    if (schema.minLength != null && value.length < schema.minLength) addError(errors, path, `must have length >= ${schema.minLength}`);
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) addError(errors, path, `must match ${schema.pattern}`);
    if (schema.format === 'date-time' && Number.isNaN(Date.parse(value))) addError(errors, path, 'must be a valid date-time');
  }

  if (typeof value === 'number') {
    if (schema.minimum != null && value < schema.minimum) addError(errors, path, `must be >= ${schema.minimum}`);
    if (schema.maximum != null && value > schema.maximum) addError(errors, path, `must be <= ${schema.maximum}`);
  }

  if (Array.isArray(value)) {
    if (schema.uniqueItems) {
      const seen = new Set(value.map((item) => JSON.stringify(item)));
      if (seen.size !== value.length) addError(errors, path, 'must contain unique items');
    }
    if (schema.items) value.forEach((item, index) => validateNode(item, schema.items, `${path}[${index}]`, errors));
    return;
  }

  if (typeof value === 'object') {
    for (const key of schema.required ?? []) {
      if (!(key in value)) addError(errors, `${path}.${key}`, 'is required');
    }
    for (const [key, child] of Object.entries(schema.properties ?? {})) {
      if (key in value) validateNode(value[key], child, `${path}.${key}`, errors);
    }
    if (schema.additionalProperties === false) {
      const allowed = new Set(Object.keys(schema.properties ?? {}));
      for (const key of Object.keys(value)) if (!allowed.has(key)) addError(errors, `${path}.${key}`, 'is not allowed');
    }
  }
}

export function validateAgainstSchema(value, schema) {
  const errors = [];
  validateNode(value, schema, '$', errors);
  return { valid: errors.length === 0, errors };
}

export function assertSchemaValid(value, schema, label = 'record') {
  const result = validateAgainstSchema(value, schema);
  if (!result.valid) {
    const error = new Error(`${label} failed schema validation.`);
    error.name = 'SchemaValidationError';
    error.validationErrors = result.errors;
    throw error;
  }
  return value;
}
