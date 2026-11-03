import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decodePacket } from '../../src/web_client/protocol.mjs';

const counts = { bolt: 1, nut: 0, washer: 0 };
const zero = { bolt: 0, nut: 0, washer: 0 };
const packet = () => ({ version: 1, mode: 'LIVE', session_id: 'board-session', config_id: 2,
  check_id: 3, frame_id: 4, width: 1280, height: 720, created_at: 1, prototype: false,
  status: 'CHECK_PASS', targets: [{ target_id: 7, bbox: [10, 20, 1280, 720], class: 'bolt', score: .9 }],
  decision: { expected: counts, actual: counts, delta: zero, missing: zero, extra: zero, reasons: [] } });
const decode = (p) => decodePacket(p, 'board-session', 2);

test('LIVE keeps board IDs, half-open boxes, verdict and actual order', () => {
  const r = decode(packet());
  assert.deepEqual(r.targets[0], { t: 'T7', cls: 'bolt', score: .9, box: [10, 20, 1270, 700] });
  assert.equal(r.verdict, 'CHECK_PASS');
  assert.deepEqual(r.expected, counts);
});

test('target_limit keeps counts unknown', () => {
  const p = packet(); p.status = 'RECHECK'; p.decision.reasons = ['target_limit'];
  assert.equal(decode(p).counts, null);
});

test('RECHECK preserves the low-confidence reason alongside order differences', () => {
  const p = packet(); p.status = 'RECHECK'; p.decision.reasons = ['low_score'];
  assert.match(decode(p).missing, /low_score/);
  assert.throws(() => decodePacket({ ...p, session_id: null }, null, 2));
});

test('reject mismatched sessions/config, malformed boxes, duplicate IDs and invalid verdicts', () => {
  const changes = [p => p.session_id = 'old', p => p.config_id = 1,
    p => p.targets[0].bbox[2] = 1281, p => p.targets.push(p.targets[0]),
    p => p.targets[0].score = NaN, p => p.status = 'PASS',
    p => p.decision.verdict = 'CHECK_FAIL', p => p.decision.actual = null,
    p => p.targets[0].class = '<b>bolt</b>', p => p.mode = 'MOCK'];
  for (const change of changes) { const p = packet(); change(p); assert.throws(() => decode(p)); }
});

test('trigger_ref matches Python optional string and 64 code point limit', () => {
  for (const ref of [null, 'manual', '😀'.repeat(64)]) {
    const p = packet(); p.trigger_ref = ref; decode(p);
  }
  for (const ref of [{}, [], 1, '', 'a'.repeat(65), '😀'.repeat(65)]) {
    const p = packet(); p.trigger_ref = ref; assert.throws(() => decode(p));
  }
});
