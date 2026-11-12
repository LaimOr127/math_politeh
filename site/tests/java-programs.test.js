import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('Java examples compile and final project matches reference DAGs and HTTP contract',()=>{
 const run=spawnSync(process.env.PYTHON||(process.platform==='win32'?'python':'python3'),['-I','-X','utf8',fileURLToPath(new URL('../../java-course/scripts/verify_java.py',import.meta.url))],{encoding:'utf8',timeout:120000});
 assert.equal(run.status,0,run.stderr||String(run.error));
});
