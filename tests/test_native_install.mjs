// Actual Hermes Electron resolver/probe, no browser or DMS access.
import assert from 'node:assert/strict';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
const root=fileURLToPath(new URL('../',import.meta.url));
const modulePath=process.env.HERMES_NATIVE_PLUGIN_DETECTOR;
const git=process.env.HERMES_TEST_GIT;
assert.ok(modulePath && git,'Supply installed Hermes detector and Git; do not guess machine paths');
const native=await import(pathToFileURL(modulePath).href);
const remote='https://github.com/lqv221998-design/hermes-plugin-dms-fast';
assert.deepEqual(native.resolvePluginGitUrl(remote),{gitUrl:remote,subdir:null});
const result=await native.detectPluginComponents(root);
assert.equal(result.agent,true);assert.equal(result.agentName,'dms-fast');assert.equal(result.desktop,true);assert.equal(result.desktopSourceSubdir,'desktop');
const scratch=process.env.TMPDIR;
assert.ok(scratch,'Use explicit managed scratch directory');
const repo=await fs.mkdtemp(path.join(scratch,'native-git-'));
try {
 for (const item of ['plugin.yaml','__init__.py','desktop','skills']) await fs.cp(path.join(root,item),path.join(repo,item),{recursive:true});
 execFileSync(git,['init',repo],{stdio:'pipe'});
 execFileSync(git,['-C',repo,'add','.'],{stdio:'pipe'});
 execFileSync(git,['-C',repo,'-c','user.name=Hermes integration fixture','-c','user.email=fixture@example.invalid','commit','-m','Native package fixture'],{stdio:'pipe'});
 const localGitUrl=process.platform==='win32'?'file://'+repo.replaceAll('\\','/'):pathToFileURL(repo).href;
 const probe=await native.probePluginRepo(git,localGitUrl);
 assert.equal(probe.ok,true,JSON.stringify(probe));assert.equal(probe.agent,true);assert.equal(probe.desktop,true);assert.equal(probe.agentName,'dms-fast');
 console.log(JSON.stringify({nativeRootDetection:result,actualNativeGitProbe:probe,network:false,dmsRead:false}));
} finally { await fs.rm(repo,{recursive:true,force:true}); }
