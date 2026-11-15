// Local-only syntax oracle. Reads CHelper from an external directory; no parser data is copied.
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

const dir=process.env.CHELPER_DIR;
if(!dir){console.error('set CHELPER_DIR to the local CHelper tool directory');process.exit(2)}
const specPath=process.argv[2];
if(!specPath){console.error('usage: node chelper_check.mjs spec.json [version]');process.exit(2)}
const version=process.argv[3] || 'netease-vanilla-1.21.50.07-Bk2sRATg.cpack';
const {createEngine}=await import(pathToFileURL(path.join(dir,'engine.mjs')).href);
const e=await createEngine(version);
const spec=JSON.parse(fs.readFileSync(specPath,'utf8'));
const cmds=[];
for(const ch of spec.chains||[]) for(const c of ch.cmds||[]) if(!c.includes('{RESET}')) cmds.push({chain:ch.id,cmd:c});
for(const b of spec.blocks||[]) if(b.command && !b.command.includes('{RESET}')) cmds.push({chain:'blocks',cmd:b.command});
const bad=[]; let ok=0;
for(const {chain,cmd} of cmds){
  try{
    const r=e.inspect(cmd);
    if(r && (!r.errorReasons || r.errorReasons.length===0)) ok++;
    else bad.push({chain,cmd,reasons:r?.errorReasons||[{reason:'no parse result'}]});
  }catch(err){bad.push({chain,cmd,reasons:[{reason:String(err)}]})}
}
const out={version,total:cmds.length,ok,fail:bad.length,bad:bad.slice(0,80)};
console.log(JSON.stringify(out,null,1));
fs.writeFileSync(path.join(path.dirname(specPath),'syntax-report.json'),JSON.stringify(out,null,1));
