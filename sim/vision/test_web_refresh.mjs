import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { decodePacket } from '../../src/web_client/protocol.mjs';

const html = await readFile(new URL('../../src/web_client/index.html', import.meta.url), 'utf8');
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]));
const source = html.match(/<script type="module">([\s\S]*?)<\/script>/)[1].replace(/^import .*;\s*$/gm, '');
const packet = JSON.parse(await readFile(new URL('../../data/logs/2026-10-30-web-live/packet.json', import.meta.url), 'utf8'));
const response = (body) => ({ ok: true, json: async () => body });
function element() {
  return { style: {}, dataset: {}, children: [], hidden: false,
    addEventListener(name, handler) { (this.listeners ||= {})[name] = handler; },
    querySelector: element, append(...items) { this.children.push(...items); },
    appendChild(item) { this.children.push(item); }, set innerHTML(value) { this.children = []; } };
}
async function setup() {
  const nodes = new Map(), requests = [];
  const node = (selector) => {
    assert.ok(selector.startsWith('#') && ids.has(selector.slice(1)), `Missing DOM element: ${selector}`);
    if (!nodes.has(selector)) nodes.set(selector, element());
    return nodes.get(selector);
  };
  const context = vm.createContext({ decodePacket, clock: 1000, location: { origin: 'http://localhost' },
    document: { querySelector: node, querySelectorAll: () => [], createElement: element,
      addEventListener() {}, documentElement: { dataset: { theme: 'dark' } } },
    navigator: {}, crypto: { randomUUID: () => 'manual-ref' }, AbortSignal: { timeout: () => undefined },
    setInterval() {}, clearInterval() {}, setTimeout() {}, clearTimeout() {},
    fetch: (path, options) => path === '/v1/check' ? new Promise((resolve, reject) => requests.push({ resolve, reject, options }))
      : Promise.resolve(response(path === '/v1/status' ? { mode: 'LIVE', hardware_connected: true,
        session_id: packet.session_id, prototype: false } : { mode: 'LIVE', applied_config_id: packet.config_id })) });
  context.performance = { now: () => context.clock };
  vm.runInContext(source, context, { filename: 'index.html' });
  await new Promise(setImmediate); // Finish the real startup handshake's promise chain.
  context.seed = { ...decodePacket(packet, packet.session_id, packet.config_id), ts: 1000, trigger: 'auto' };
  vm.runInContext('state.result=seed; state.auto=true; videoReady=true; snapshotReady=true; renderAll()', context);
  const ui = vm.runInContext('({state,liveRound,freshnessLoop,setMode,snapshot})', context);
  return { context, nodes, requests, ui, complete: (extra = {}) => requests[0].resolve(response({ ...packet, check_id: 2, ...extra })) };
}

test('an in-flight refresh retains the last valid result and its original age', async () => {
  const t = await setup(), old = t.ui.state.result, pending = t.ui.liveRound(false);
  assert.equal(t.ui.state.result, old); assert.equal(old.ts, 1000);
  assert.equal(t.nodes.get('#targets').children.length, packet.targets.length);
  t.complete(); await pending;
});
test('success replaces the result; automatic rounds never add records', async () => {
  const t = await setup(), pending = t.ui.liveRound(false); t.context.clock = 1300;
  t.complete(); await pending;
  assert.equal(t.ui.state.result.check, 2); assert.equal(t.ui.state.result.ts, 1300);
  assert.equal(t.ui.state.records.length, 0); assert.equal(t.ui.state.rec, 0);
});
test('a slow request cannot keep expired results visible', async () => {
  const t = await setup(), pending = t.ui.liveRound(false);
  t.context.clock = 1000 + t.ui.state.maxAge; t.ui.freshnessLoop();
  assert.equal(t.ui.state.result, null); assert.equal(t.nodes.get('#targets').children.length, 0);
  t.complete(); await pending;
});
test('manual failure removes the old result and pauses automatic checks', async () => {
  const t = await setup(), pending = t.ui.liveRound(true);
  t.requests[0].reject(new Error('board unavailable')); await pending;
  assert.equal(t.ui.state.result, null); assert.equal(t.ui.state.manualFail, true);
  assert.equal(t.ui.state.auto, false); assert.equal(t.ui.state.rec, 0);
});
test('switching mode rejects a delayed response from the old epoch', async () => {
  const t = await setup(), pending = t.ui.liveRound(false); t.ui.setMode('replay');
  t.complete(); await pending;
  assert.equal(t.ui.state.mode, 'replay'); assert.equal(t.ui.state.result, null);
  assert.equal(t.ui.state.round, 0); assert.equal(t.ui.state.rec, 0);
});
test('repeated timer ticks never submit concurrent checks', async () => {
  const t = await setup(), pending = t.ui.liveRound(false); await t.ui.liveRound(false);
  assert.equal(t.requests.length, 1); t.complete(); await pending;
});
test('new boxes stay hidden until the matching board snapshot loads', async () => {
  const t = await setup(); vm.runInContext('videoReady=false; renderAll()', t.context);
  const pending = t.ui.liveRound(false); assert.equal(t.ui.snapshot.hidden, false);
  t.complete(); await pending;
  assert.equal(t.ui.snapshot.hidden, true); assert.equal(t.nodes.get('#targets').children.length, 0);
  t.ui.snapshot.onload();
  assert.equal(t.ui.snapshot.hidden, false); assert.equal(t.nodes.get('#targets').children.length, packet.targets.length);
});
test('500 ms mode starts immediately and UVC does not download per-round PNGs', async () => {
  const t = await setup(); assert.equal(t.ui.state.interval, 500);
  t.nodes.get('#sel-auto').listeners.change({ target: { checked: true } });
  assert.equal(t.requests.length, 1); t.complete(); await new Promise(setImmediate);
  assert.equal(t.ui.state.result.check, 2); assert.equal(t.ui.snapshot.src, undefined);
});
test('fast polling keeps offline reconnection attempts two seconds apart', async () => {
  const t = await setup(); let attempts = 0; t.ui.state.connected = false;
  t.context.fetch = async () => { attempts++; throw new Error('offline'); };
  for (const clock of [3000, 3500, 4500]) {
    t.context.clock = clock; vm.runInContext('autoRound()', t.context); await new Promise(setImmediate);
  }
  assert.equal(attempts, 1);
  t.context.clock = 5000; vm.runInContext('autoRound()', t.context); await new Promise(setImmediate);
  assert.equal(attempts, 2);
});

test('same-session configuration refresh is read-only and recovers the next round', async () => {
  const t = await setup(); let writes = 0;
  vm.runInContext("manualRef='previous-config-intent'", t.context);
  t.context.fetch = async (path, options) => {
    if (options?.method === 'POST') writes++;
    return response(path === '/v1/status' ? {mode:'LIVE',hardware_connected:true,
      session_id:packet.session_id,config_id:packet.config_id+1,prototype:false}
      : {...packet,config_id:packet.config_id+1});
  };
  t.context.clock = 3000; vm.runInContext('autoRound()', t.context);
  await new Promise(setImmediate);
  assert.equal(writes, 0); assert.equal(t.ui.state.config, packet.config_id+1);
  assert.equal(t.ui.state.result, null);
  assert.equal(vm.runInContext('manualRef', t.context), null);
  await t.ui.liveRound(false);
  assert.equal(t.ui.state.connected, true);
  assert.equal(t.ui.state.result.cfg, packet.config_id+1);
});

test('an invalid status config is rejected without a configuration write', async () => {
  const t = await setup(); let writes = 0;
  t.context.fetch = async (_path, options) => {
    if (options?.method === 'POST') writes++;
    return response({mode:'LIVE',hardware_connected:true,
      session_id:packet.session_id,config_id:-1});
  };
  t.context.clock = 3000; vm.runInContext('autoRound()', t.context);
  await new Promise(setImmediate);
  assert.equal(writes, 0); assert.equal(t.ui.state.connected, false);
  assert.equal(t.ui.state.result, null);
});

test('unchanged status retains the retry intent and original result age', async () => {
  const t = await setup(), old = t.ui.state.result;
  vm.runInContext("manualRef='same-config-retry'", t.context);
  t.context.fetch = async () => response({mode:'LIVE',hardware_connected:true,
    session_id:packet.session_id,config_id:packet.config_id});
  t.context.clock = 3000; vm.runInContext('autoRound()', t.context);
  await new Promise(setImmediate);
  assert.equal(t.ui.state.result, old); assert.equal(old.ts, 1000);
  assert.equal(vm.runInContext('manualRef', t.context), 'same-config-retry');
});

test('idle heartbeat detects hardware loss and clears the result', async () => {
  const t = await setup(); t.ui.state.auto = false;
  t.context.fetch = async () => response({mode:'LIVE',hardware_connected:false,
    session_id:packet.session_id,config_id:packet.config_id});
  t.context.clock = 3000; vm.runInContext('autoRound()', t.context);
  await new Promise(setImmediate);
  assert.equal(t.ui.state.connected, false); assert.equal(t.ui.state.result, null);
});
