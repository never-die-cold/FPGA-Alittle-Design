const classes = ['bolt', 'nut', 'washer'];
const uint = (n) => Number.isInteger(n) && n >= 0 && n <= 0xffffffff;
const fields = ['version', 'mode', 'session_id', 'config_id', 'check_id', 'frame_id',
  'width', 'height', 'created_at', 'status', 'targets', 'decision', 'prototype', 'trigger_ref'];

export function decodePacket(p, session, config) {
  const invalid = () => { throw new Error('无效或过期的板端报文'); };
  if (!p || Object.keys(p).some((k) => !fields.includes(k)) || p.version !== 1 || p.mode !== 'LIVE'
      || typeof p.session_id !== 'string' || !p.session_id || p.session_id !== session || p.config_id !== config
      || ![p.check_id, p.frame_id, p.config_id].every(uint)
      || !Number.isFinite(p.created_at) || (p.prototype !== undefined && typeof p.prototype !== 'boolean')
      || (p.trigger_ref != null && (typeof p.trigger_ref !== 'string'
          || p.trigger_ref.length < 1 || [...p.trigger_ref].length > 64))
      || !Number.isInteger(p.width) || p.width < 1 || p.width > 4096
      || !Number.isInteger(p.height) || p.height < 1 || p.height > 2160
      || !Array.isArray(p.targets) || p.targets.length > 16) invalid();
  const ids = new Set();
  const targets = p.targets.map((t) => {
    if (!t || Object.keys(t).some((k) => !['target_id', 'bbox', 'class', 'score'].includes(k))
        || !uint(t.target_id) || ids.has(t.target_id) || !Array.isArray(t.bbox)
        || t.bbox.length !== 4 || !t.bbox.every(Number.isInteger)
        || (t.class != null && !classes.includes(t.class))
        || (t.score !== undefined && (!Number.isFinite(t.score) || t.score < 0 || t.score > 1))) invalid();
    ids.add(t.target_id);
    const [x0, y0, x1, y1] = t.bbox;
    if (!(0 <= x0 && x0 < x1 && x1 <= p.width && 0 <= y0 && y0 < y1 && y1 <= p.height)) invalid();
    return { t: `T${t.target_id}`, cls: t.class ?? null, score: t.score ?? null,
      box: [x0, y0, x1 - x0, y1 - y0] };
  });
  if (!['CHECK_PASS', 'CHECK_FAIL', 'RECHECK', 'LOCATION_ONLY'].includes(p.status)) invalid();
  const d = p.decision;
  if (p.status === 'LOCATION_ONLY') {
    if (d !== undefined) invalid();
  } else {
    if (!d || Object.keys(d).some((k) => !['verdict', 'expected', 'actual', 'delta', 'missing', 'extra', 'reasons'].includes(k))
        || (d.verdict !== undefined && d.verdict !== p.status)
        || !Array.isArray(d.reasons) || d.reasons.some((v) => typeof v !== 'string' || !v)) invalid();
    for (const k of ['expected', 'actual', 'delta', 'missing', 'extra']) {
      if (!d[k] || Object.keys(d[k]).length !== 3 || !classes.every((c) => Number.isInteger(d[k][c])
          && (k === 'delta' || d[k][c] >= 0))) invalid();
    }
  }
  const limited = d?.reasons.includes('target_limit');
  const difference = d ? classes.flatMap((c) => [d.missing[c] ? `-${c}×${d.missing[c]}` : '',
    d.extra[c] ? `+${c}×${d.extra[c]}` : '']).filter(Boolean).join(' ') : '';
  return { targets, counts: limited ? null : d?.actual ?? null, expected: d?.expected,
    verdict: p.status, kind: p.status === 'CHECK_PASS' ? 'pass' : p.status === 'CHECK_FAIL' ? 'fail' : 'warn',
    missing: limited ? '未完整计数 · target_limit' : [difference, ...(d?.reasons || [])].filter(Boolean).join(' · '),
    check: p.check_id, cfg: p.config_id, width: p.width, height: p.height, packet: p };
}
