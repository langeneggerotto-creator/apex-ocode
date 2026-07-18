import fs from 'node:fs';
import path from 'node:path';

function balanced(source, open, close) {
  let depth = 0;
  for (const character of source) {
    if (character === open) depth += 1;
    if (character === close) depth -= 1;
    if (depth < 0) return false;
  }
  return depth === 0;
}

export function validateGeneratedSource(implementationDirectory) {
  const screen = fs.readFileSync(path.join(implementationDirectory, 'DreamIntakeScreen.tsx'), 'utf8');
  const model = fs.readFileSync(path.join(implementationDirectory, 'dream-intake-model.ts'), 'utf8');
  const storage = fs.readFileSync(path.join(implementationDirectory, 'dream-intake-storage.ts'), 'utf8');
  const checks = {
    screen_default_export: /export default function DreamIntakeScreen/.test(screen),
    react_native_import: /from 'react-native'/.test(screen),
    async_storage_adapter: /@react-native-async-storage\/async-storage/.test(screen),
    one_screen_only: !/NavigationContainer|createStackNavigator|router\./.test(screen),
    exactly_one_question_render: (screen.match(/\{nextQuestion\}/g) ?? []).length === 1,
    model_exports_card_builder: /export function createDreamCard/.test(model),
    model_exports_correction: /export function applyDreamCorrection/.test(model),
    storage_exports_draft_store: /export class DreamDraftStore/.test(storage),
    no_any_type: !/\bany\b/.test(`${screen}\n${model}\n${storage}`),
    balanced_braces: balanced(`${screen}\n${model}\n${storage}`, '{', '}'),
    balanced_parentheses: balanced(`${screen}\n${model}\n${storage}`, '(', ')')
  };
  const failed = Object.entries(checks).filter(([, passed]) => !passed).map(([id]) => id);
  return {
    validator_version: '0.3',
    checks,
    passed: failed.length === 0,
    failed,
    truth_status: failed.length === 0 ? 'STRUCTURALLY_VALIDATED_NOT_BUNDLED' : 'SOURCE_REPAIR_REQUIRED',
    boundary: 'This validator checks the generated source contract and structure. It is not an Expo bundler, TypeScript compiler, simulator, or physical-device test.'
  };
}
