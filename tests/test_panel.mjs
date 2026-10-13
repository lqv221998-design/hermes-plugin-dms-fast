import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const path = new URL('../desktop-plugins/dms-fast-panel/plugin.js', import.meta.url);
assert.equal(await fs.access(path).then(()=>true,()=>false), true, 'Missing DMS desktop panel');
const source = await fs.readFile(path, 'utf8');
assert.ok(!source.includes('dms_fast_read'), 'Pane must never request the direct reader');
assert.ok(source.includes('dms_fast_session'), 'Pane must use the resumable session entry');
let inserted = [];
let notices = [];
let registered = [];
let submitted = [];
let busy = {};
let values = [];
const host = {state:{focusedSessionId:{get:()=> 'test-session'},busyBySession:{get:()=>busy}},composer:{insertText:async(...args)=>{inserted.push(args);return true;},submit:(...args)=>{submitted.push(args);return true;}},notify:x=>notices.push(x)};
const ctx = {register:x=>registered.push(x)};
const testSource = source
  .replace(/import[^;]+from '@hermes\/plugin-sdk';/, 'const {host} = globalThis.__dmsTest;')
  .replace(/import[^;]+from 'react';/, 'const useState = globalThis.__dmsTest.useState;')
  .replace(/import[^;]+from 'react\/jsx-runtime';/, 'const jsx = (type, props) => ({type,props});');
globalThis.__dmsTest = {host,useState:x=>[values.length?values.shift():x,()=>{}]};
const {default:plugin} = await import('data:text/javascript;base64,'+Buffer.from(testSource).toString('base64'));
plugin.register(ctx);
const pane = registered.find(x=>x.area==='panes');
assert.ok(pane);
const root = pane.render();
const tree = typeof root.type==='function' ? root.type(root.props) : root;
let buttons=[];
function walk(x){if(!x)return;if(Array.isArray(x)){x.forEach(walk);return;}if(typeof x==='object'){if(x.type==='button')buttons.push(x);walk(x.props?.children);}}
walk(tree);
assert.ok(buttons.length >= 5);
// No page ID guessed: operation controls disabled at first render.
assert.ok(buttons.filter(x=>x.props['data-dms-action']).every(x=>x.props.disabled===true));
const skill = buttons.find(x=>x.props.children==='Nạp skill đọc DMS');
await skill.props.onClick();
assert.equal(inserted.length,1);
assert.equal(inserted[0][0],null);
assert.match(inserted[0][1], /dms-fast:reading/);
assert.equal(inserted[0][2].mode,'block');
assert.equal(notices.length,1);
values = ['fast-work','Quy trình',''];
buttons = [];
walk(root.type(root.props));
const search = buttons.find(x=>x.props['data-dms-action']==='search');
assert.equal(search.props.disabled,false);
await search.props.onClick();
assert.equal(submitted.length,1,'Search should submit once without an extra Send/Run step');
assert.equal(submitted[0][0],'test-session');
assert.match(submitted[0][1],/dms_fast_session/);
assert.match(submitted[0][1],/fast-work/);
assert.match(submitted[0][1],/"kind":"search"/,'Search button must request an explicit non-download task');
const inspect = buttons.find(x=>x.props['data-dms-action']==='inspect');
assert.ok(inspect, 'Panel needs state-preserving UI inspection');
await inspect.props.onClick();
assert.equal(submitted.length,2);
assert.match(submitted[1][1],/"action":"inspect"/);
const menuKeys = ['internal','departments','sites','charts','grid','booking','guides'];
for (const key of menuKeys) {
  const menu = buttons.find(x=>x.props['data-dms-action']===`menu-${key}`);
  assert.ok(menu, `Missing read menu ${key}`);
  const before = submitted.length;
  await menu.props.onClick();
  assert.equal(submitted.length,before+1);
  assert.match(submitted.at(-1)[1],/"action":"inspect"/);
  assert.ok(submitted.at(-1)[1].includes(`"menu":"${key}"`));
}
busy = {'test-session':true};
await search.props.onClick();
assert.equal(submitted.length,2+menuKeys.length,'A busy session must not enqueue duplicate browser work');
assert.ok(!source.includes('ctx.rest'));
console.log('PASS: panel registration, user-click single-submit search, busy guard, draft-only skill action; no browser/backend side door');
