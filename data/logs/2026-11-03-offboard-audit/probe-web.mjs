// Audit only: reuse the repository's real page VM harness; no product mutation.
// Run from repository root: node --test data/logs/2026-11-03-offboard-audit/probe-web.mjs
import { readFile } from 'node:fs/promises';
const original = new URL('../../../sim/vision/test_web_refresh.mjs', import.meta.url);
let source = await readFile(original, 'utf8');
source = source.replaceAll('import.meta.url', JSON.stringify(original.href));
source = source.replace("'../../src/web_client/protocol.mjs'",
  JSON.stringify(new URL('../../../src/web_client/protocol.mjs', import.meta.url).href));
source += `
test('AUDIT: same-session config change cannot recover by reconnecting', async () => {
  const t = await setup(), pending = t.ui.liveRound(false);
  t.complete({config_id: packet.config_id + 1}); await pending;
  assert.equal(t.ui.state.connected, false);
  let configRequests = 0;
  t.context.fetch = async (path) => {
    if (path === '/v1/config') configRequests++;
    return response(path === '/v1/status'
      ? {mode:'LIVE',hardware_connected:true,session_id:packet.session_id,prototype:false}
      : {...packet,config_id:packet.config_id + 1});
  };
  await vm.runInContext('connectLive()', t.context);
  assert.equal(t.ui.state.connected, true);
  assert.equal(configRequests, 0);
  assert.equal(t.ui.state.config, packet.config_id);
  await t.ui.liveRound(false);
  assert.equal(t.ui.state.connected, false);
  console.log('REPRODUCED: reconnect skips config refresh; next real round fails again');
});
test('AUDIT: JS parser accepts an invalid trigger_ref object', () => {
  const p = {...packet,trigger_ref:{invalid:true}};
  assert.equal(decodePacket(p,p.session_id,p.config_id).packet,p);
  console.log('REPRODUCED: trigger_ref object accepted by JS schema parser');
});
`;
await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
