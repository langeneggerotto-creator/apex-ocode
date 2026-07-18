import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const htmlPath = join(here, '../../universal-wrapper/mobile-web-preview/index.html');
const html = await readFile(htmlPath, 'utf8');

const requiredIds = [
  'dream-input',
  'save-review',
  'dream-card',
  'original-dream',
  'interpreted-outcome',
  'correction-input',
  'apply-correction',
  'one-next-question',
  'create-receipt'
];

const failures = [];
for (const id of requiredIds) {
  if (!html.includes(`id="${id}"`)) failures.push(`missing required element #${id}`);
}

const contractMatch = html.match(/<script id="ocode-semantic-contract" type="application\/json">([\s\S]*?)<\/script>/);
if (!contractMatch) {
  failures.push('missing embedded semantic contract');
} else {
  const contract = JSON.parse(contractMatch[1]);
  const requiredBehaviors = [
    'dream_entry',
    'draft_persistence',
    'structured_dream_card',
    'dreamer_correction_preserves_original',
    'exactly_one_next_question'
  ];
  for (const behavior of requiredBehaviors) {
    if (!contract.requiredBehaviors.includes(behavior)) failures.push(`semantic contract missing ${behavior}`);
  }
}

if (!html.includes('localStorage.setItem(DRAFT_KEY')) failures.push('draft persistence write is missing');
if (!html.includes('localStorage.getItem(DRAFT_KEY)')) failures.push('draft persistence restore is missing');
if (!html.includes('originalDream: dream')) failures.push('original dream preservation is missing');
if (!html.includes('interpretedOutcome: correction')) failures.push('correction does not update interpretation');
if (!html.includes('revisionHistory: [...card.revisionHistory')) failures.push('correction history preservation is missing');
if (/\bfetch\s*\(/.test(html) || /XMLHttpRequest/.test(html)) failures.push('bounded preview must not transmit dream data');

const questionMatch = html.match(/<div class="question" id="one-next-question">[\s\S]*?<p>([^<]+)<\/p>/);
if (!questionMatch) failures.push('one next question text is missing');
else if ((questionMatch[1].match(/\?/g) ?? []).length !== 1) failures.push('the next-question component must contain exactly one question');

const checkCount = (html.match(/data-check="/g) ?? []).length;
if (checkCount !== 8) failures.push(`expected 8 phone proof checks, found ${checkCount}`);

if (failures.length > 0) {
  console.error(JSON.stringify({ status: 'FAIL', failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  status: 'PASS',
  htmlPath,
  requiredElementCount: requiredIds.length,
  phoneCheckCount: checkCount,
  networkTransmissionDetected: false,
  semanticBehaviorCount: 5,
  truthStatus: 'STRUCTURAL_AND_STATIC_BEHAVIOR_VALIDATION__BROWSER_INTERACTION_NOT_YET_EXECUTED'
}, null, 2));
