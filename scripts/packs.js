#!/usr/bin/env node
// Helper for puzzle packs (packs/<id>/NNN.json).
//
//   node scripts/packs.js verify [--show]
//       Checks every pack listed in packs/index.json: files exist, words
//       decode, lengths match `size`, the triangle constraints hold and no
//       word repeats within a pack. --show prints the decoded answers.
//
//   node scripts/packs.js add <packId> "<Category>" <wordOne> <wordTwo> <wordThree>
//       Verifies the triangle, writes the next NNN.json with base64-encoded
//       words and bumps the pack's count in packs/index.json.

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const INDEX = path.join(ROOT, 'packs', 'index.json');

const encode = (w) => Buffer.from(w, 'utf8').toString('base64');
const decode = (w) => Buffer.from(w, 'base64').toString('utf8');
const puzzleFile = (packId, n) => path.join(ROOT, 'packs', packId, `${String(n).padStart(3, '0')}.json`);

function triangleErrors(one, two, three) {
  const errors = [];
  if (!(one.length === two.length && two.length === three.length)) errors.push('words are not the same length');
  if (![4, 5].includes(one.length)) errors.push('words must be 4 or 5 letters');
  if (one[one.length - 1] !== two[0]) errors.push(`apex: ${one} ends "${one.at(-1)}" but ${two} starts "${two[0]}"`);
  if (one[0] !== three[0]) errors.push(`bottom-left: ${one} starts "${one[0]}" but ${three} starts "${three[0]}"`);
  if (two[two.length - 1] !== three[three.length - 1]) errors.push(`bottom-right: ${two} ends "${two.at(-1)}" but ${three} ends "${three.at(-1)}"`);
  return errors;
}

function readWords(game) {
  const get = (w) => (game.encoded ? decode(w ?? '') : (w ?? '')).toLowerCase();
  return [get(game.wordOne), get(game.wordTwo), get(game.wordThree)];
}

function verify(show) {
  const packs = JSON.parse(fs.readFileSync(INDEX, 'utf8'));
  let failures = 0;

  for (const pack of packs) {
    console.log(`\n${pack.title} (${pack.id}) — ${pack.count} puzzles`);
    const seen = new Map();

    for (let n = 1; n <= pack.count; n++) {
      const file = puzzleFile(pack.id, n);
      const label = `  ${String(n).padStart(3, '0')}`;
      if (!fs.existsSync(file)) {
        console.log(`${label} MISSING ${path.relative(ROOT, file)}`);
        failures++;
        continue;
      }
      const game = JSON.parse(fs.readFileSync(file, 'utf8'));
      const words = readWords(game);
      const errors = triangleErrors(...words);
      const size = game.size ?? 5;
      if (words[0].length !== size) errors.push(`size is ${size} but words have ${words[0].length} letters`);
      if (!game.category) errors.push('missing category');
      for (const w of words) {
        if (seen.has(w)) errors.push(`"${w}" already used in puzzle ${seen.get(w)}`);
        seen.set(w, n);
      }

      const answer = show ? `  ${words.join(' / ')}` : '';
      if (errors.length) {
        failures++;
        console.log(`${label} ✗ ${game.category}${answer}`);
        errors.forEach((e) => console.log(`        ${e}`));
      } else {
        console.log(`${label} ✓ ${game.category}${answer}`);
      }
    }
  }

  if (failures) {
    console.log(`\n${failures} problem(s) found`);
    process.exit(1);
  }
  console.log('\nAll packs OK');
}

function add(packId, category, ...words) {
  words = words.map((w) => (w ?? '').toLowerCase());
  if (!packId || !category || words.length !== 3 || words.some((w) => !/^[a-z]+$/.test(w))) {
    console.error('usage: node scripts/packs.js add <packId> "<Category>" <wordOne> <wordTwo> <wordThree>');
    process.exit(1);
  }
  const errors = triangleErrors(...words);
  if (errors.length) {
    errors.forEach((e) => console.error(e));
    process.exit(1);
  }

  const packs = JSON.parse(fs.readFileSync(INDEX, 'utf8'));
  const pack = packs.find((p) => p.id === packId);
  if (!pack) {
    console.error(`No pack "${packId}" in packs/index.json — add an entry first (id, title, description, count: 0).`);
    process.exit(1);
  }

  const n = pack.count + 1;
  const game = { category };
  if (words[0].length === 4) game.size = 4;
  game.encoded = true;
  game.wordOne = encode(words[0]);
  game.wordTwo = encode(words[1]);
  game.wordThree = encode(words[2]);

  fs.mkdirSync(path.dirname(puzzleFile(packId, n)), { recursive: true });
  fs.writeFileSync(puzzleFile(packId, n), JSON.stringify(game, null, 4) + '\n');
  pack.count = n;
  fs.writeFileSync(INDEX, JSON.stringify(packs, null, 4) + '\n');
  console.log(`Wrote ${path.relative(ROOT, puzzleFile(packId, n))} (${category})`);
}

const [command, ...args] = process.argv.slice(2);
if (command === 'verify') verify(args.includes('--show'));
else if (command === 'add') add(...args);
else {
  console.error('usage: node scripts/packs.js verify [--show] | add <packId> "<Category>" <w1> <w2> <w3>');
  process.exit(1);
}
