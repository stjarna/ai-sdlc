#!/usr/bin/env python3
"""Render and audit documentation SVGs with local Chrome (no added dependencies).

Examples:
  python3 docs/assets/verify_workflow.py
  python3 docs/assets/verify_workflow.py --before FULL_COMMIT_OID
Outputs stay in ignored .tmp/workflow-preview unless --output is supplied.
"""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import generate_workflow as generator

CHECK = r'''
const svg=document.querySelector('svg');
const texts=[...svg.querySelectorAll('text')].map(t=>({text:t.textContent,kind:t.dataset.kind,box:t.getBBox(),element:t}));
const overlap=(a,b)=>Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>0.8&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>0.8;
const issues=[];
for(let i=0;i<texts.length;i++){
 const a=texts[i];
 for(let j=i+1;j<texts.length;j++)if(overlap(a.box,texts[j].box))issues.push(['text collision',a.text,texts[j].text]);
 const group=a.element.closest('[data-box]');
 if(group&&a.kind==='stage-label'){
  const [x,y,w,h]=group.dataset.box.split(',').map(Number),b=a.box;
  if(b.x<x+3||b.x+b.width>x+w-3||b.y<y+3||b.y+b.height>y+h-3)issues.push(['label outside card',a.text,group.dataset.stage]);
 }
 const b=a.box;
 if(b.x<0||b.y<0||b.x+b.width>svg.viewBox.baseVal.width||b.y+b.height>svg.viewBox.baseVal.height)issues.push(['outside canvas',a.text]);
}
for(const path of svg.querySelectorAll('[data-connector]')){
 const length=path.getTotalLength();
 for(let d=1;d<length;d+=2){
  const p=path.getPointAtLength(d);
  const t=texts.find(t=>p.x>t.box.x&&p.x<t.box.x+t.box.width&&p.y>t.box.y&&p.y<t.box.y+t.box.height);
  if(t){issues.push(['connector crosses text',t.text]);break;}
 }
}
document.querySelector('pre').textContent=JSON.stringify({issues,labels:texts.length,cards:svg.querySelectorAll('[data-box]').length,gates:svg.querySelectorAll('[data-gate]').length});
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome',default=shutil.which('google-chrome') or shutil.which('chromium') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    parser.add_argument('--output',type=Path,default=generator.ROOT/'.tmp/workflow-preview')
    parser.add_argument('--before',help='Optional immutable Git commit for a before/after preview')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    generator.validate_runtime();results={}
    def chrome(file,*options):
        run=subprocess.run([args.chrome,'--headless','--disable-gpu','--no-first-run','--hide-scrollbars',
                            '--user-data-dir='+str(out/'browser-profile'),*options,file.as_uri()],
                           capture_output=True,text=True,timeout=60)
        assert run.returncode==0,run.stderr
        return run.stdout
    for detailed,name in ((False,'overview'),(True,'detailed')):
        path=Path(__file__).with_name('workflow-'+name+'.svg');raw=path.read_text()
        assert raw==generator.Diagram(detailed).render(),f'Regenerate {path.name}'
        parsed=ET.fromstring(raw);assert parsed.attrib['role']=='img'
        assert not re.search(r'<(?:script|foreignObject|image)\b|https?://[^"\s]*\.(?:woff|ttf)',raw)
        file=out/(name+'-geometry.html');file.write_text('<!doctype html><meta charset="utf-8">'+raw+'<pre></pre><script>'+CHECK+'</script>')
        dom=chrome(file,'--virtual-time-budget=1000','--dump-dom')
        data=json.loads(html.unescape(dom.split('<pre>')[1].split('</pre>')[0]));assert not data['issues'],data
        assert data['cards']==14 and data['gates']==(19 if detailed else 12),data
        results[name]=data
        widths=[int(parsed.attrib['width'])] if detailed else [int(parsed.attrib['width']),900,768]
        for width in widths:
            height=round(width*int(parsed.attrib['height'])/int(parsed.attrib['width']))
            page=out/(name+'-'+str(width)+'.html')
            page.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0}svg{display:block;width:'+str(width)+'px;height:auto}</style>'+raw)
            chrome(page,'--window-size='+str(width)+','+str(height),'--screenshot='+str(out/(name+'-'+str(width)+'.png')))
    if args.before:
        assert re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',args.before),'Use a full commit OID'
        old=subprocess.check_output(['git','-C',str(generator.ROOT),'show',args.before+':docs/assets/workflow-overview.svg'],text=True)
        new=Path(__file__).with_name('workflow-overview.svg').read_text()
        page=out/'comparison.html'
        page.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:20px;display:flex;gap:24px;font:18px Arial;background:#fff}section{width:900px}svg{width:900px;height:auto;display:block}</style>'+
                        '<section><h2>Before</h2>'+old+'</section><section><h2>After</h2>'+new+'</section>')
        chrome(page,'--window-size=1864,690','--screenshot='+str(out/'comparison.png'))
    (out/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'output':str(out),'results':results},indent=2))


if __name__=='__main__':main()
