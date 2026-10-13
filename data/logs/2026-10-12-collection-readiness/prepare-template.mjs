import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const root = path.resolve(import.meta.dirname, '../../..');
const target = path.join(root, 'docs/fastener-collection-log-template.csv');
const source = await fs.readFile(target, 'utf8');
const workbook = await Workbook.fromCSV(source, { sheetName: 'Collection' });
const sheet = workbook.worksheets.getItem('Collection');
const original = sheet.getRange('A1:O2').values;
const write = process.argv.includes('--write');
if (original.length !== 2 || original[0].length !== 15) throw Error('Unexpected CSV layout');
if (write) {
  sheet.getRange('A2').values = [['sess-20261012-0930-l0-wood']];
  sheet.getRange('J2').values = [['bolt-a,nut-a,washer-a']];
}
workbook.recalculate();
const values = sheet.getRange('A1:O2').values;
for (let row = 0; row < 2; row++) {
  for (let col = 0; col < 15; col++) {
    if (write && row === 1 && [0, 9].includes(col)) continue;
    if (values[row][col] !== original[row][col]) throw Error('Unrelated cell changed');
  }
}
const inspected = await workbook.inspect({ kind: 'table', range: 'Collection!A1:O2',
  include: 'values,formulas', tableMaxRows: 2, tableMaxCols: 15, maxChars: 3500 });
await fs.writeFile(path.join(import.meta.dirname, write ? 'inspect-after.txt' : 'inspect-before.txt'), inspected.ndjson);
sheet.getRange('A1:O2').format.font = { name: 'Arial', size: 10 };
sheet.getRange('A1:O2').format.columnWidth = 24;
sheet.getRange('A1:O2').format.rowHeight = 32;
sheet.getRange('J1:J2').format.columnWidth = 32;
for (const [name, range] of [['identity', 'A1:E2'], ['conditions', 'F1:J2'], ['coverage', 'K1:O2']]) {
  const preview = await workbook.render({ sheetName: 'Collection', range, scale: 1.5, format: 'png' });
  await fs.writeFile(path.join(import.meta.dirname, `${name}-${write ? 'after' : 'before'}.png`),
    new Uint8Array(await preview.arrayBuffer()));
}
if (write) {
  const quote = value => /[",\r\n]/.test(String(value))
    ? '"' + String(value).replaceAll('"', '""') + '"' : String(value);
  const result = values.map(row => row.map(quote).join(',')).join('\n') + '\n';
  await fs.writeFile(target, result, 'utf8');
  console.log('PASS: 15-column CSV preserved; only session/specimens changed; LF/UTF-8');
} else {
  console.log('PASS: original CSV imported and rendered; no source edits');
}
