#!/usr/bin/env python3
"""Generate GitHub-safe workflow vectors. Run with --check for reproducibility.

Visual vocabulary: approved complete-workflow-v2-r1 master-scene.svg. Geometry is
local and declarative; no dependency on the presentation project or its toolchain.
This is an activity overview, not an executable state machine or governance policy.
"""
from pathlib import Path
from html import escape
import argparse
import ast
import json

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = 'd207b0f0fbd568660d801130f2be59959fb6760a90cfde52136ec32f95dd9c00'
COLORS = dict(navy='#193449', teal='#087e85', muted='#586f7f', border='#cbd8e1',
              background='#f5f7f9', blue='#557da9')
SHARED = [
    ('discovery', ('Discovery',), ('Discovery',), ('idea.md',), 'Requester'),
    ('business', ('Business', 'Refinement'), ('Business', 'refinement'), ('business.md',), 'Product Owner'),
    ('analysis', ('Functional', 'Analysis'), ('Functional', 'analysis'), ('specification.md',), 'Business Analyst'),
]
ENGINEERING = [
    ('design', ('Technical', 'Design'), ('Technical', 'design'), ('technical-design.md',)),
    ('plan', ('Implementation', 'Planning'), ('Planning',), ('implementation-plan.md',)),
    ('code', ('Development /', 'Code Review'), ('Develop', '& review'), ('code-review.md',)),
    ('verification', ('Engineering', 'Verification'), ('Verify',), ('Current checks +', 'QA completion')),
    ('security', ('Security', 'Review'), ('Security', 'review'), ('security-review.md',)),
    ('final', ('Final', 'Verification'), ('Final', 'verification'), ('verification-report.md',)),
]
QA = [
    ('strategy', ('Test Strategy /', 'Scenarios'), ('Test', 'design'), ('test-strategy.md', 'test-scenarios.md')),
    ('automation', ('Test', 'Automation'), ('Test', 'automation'), ('test-automation.md',)),
    ('qa-verification', ('QA', 'Verification'), ('QA', 'verification'), ('Test results + evidence',)),
]
# Each item is a separate human action, never a combined approval/advance operation.
SHARED_GATES = [('Complete Discovery',), ('Approve Business revision', 'Advance Business'),
                ('Approve Analysis revision', 'Advance Analysis and create track readiness')]
ENGINEERING_GATES = [('Approve Design revision', 'Advance Design'),
                     ('Approve Plan revision', 'Advance Plan to Development readiness'),
                     ('Approve Code Review revision', 'Advance Code to Verification'),
                     ('Advance Verification with current completed QA evidence',),
                     ('Advance after current Security Review and resolved findings',),
                     ('Explicitly finalize Engineering',)]
QA_GATES = [('Approve strategy and scenarios', 'Advance QA design'),
            ('Approve QA automation', 'Advance QA to Verification readiness'),
            ('Explicitly complete QA after current passing checks',)]


def assignments(path):
    result = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):pass  # Derived constants are not diagram inputs.
    return result


def validate_runtime():
    """Check documented forward order/names against source; no runtime mutation/import."""
    contract = assignments(ROOT/'orchestrator/scripts/engineering_contract.py')
    order = ['technical_design', 'ready_for_implementation_planning', 'implementation_planning',
             'ready_for_development', 'development', 'verification', 'security_review',
             'final_verification', 'verified']
    for a, b in zip(order, order[1:]):
        assert b in contract['TRANSITIONS'][a], (a, b)
    qa_tree = ast.parse((ROOT/'orchestrator/scripts/qa_track.py').read_text())
    qa_states = next(ast.literal_eval(n.value) for n in qa_tree.body
                     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'STATUSES')
    assert qa_states == ('ready_for_test_design', 'test_design', 'test_automation', 'ready_for_verification', 'verified')
    names = assignments(ROOT/'orchestrator/scripts/artifact_names.py')['NAMES']
    documented = {n for stage in [SHARED, ENGINEERING, QA] for item in stage for n in item[3] if n.endswith('.md')}
    assert documented <= {v[0] for v in names.values()}
    tracks = (ROOT/'orchestrator/scripts/work_tracks.py').read_text()
    assert 'Engineering Lead' in tracks and 'QA Lead / Tester' in tracks


class Diagram:
    def __init__(self, detailed):
        self.detailed = detailed
        self.w, self.h = (2740, 1280) if detailed else (1700, 864)
        self.margin = 40 if detailed else 32
        self.cw, self.ch, self.gap = (194, 128, 72) if detailed else (116, 112, 46)
        self.sx = self.margin
        self.ex = self.sx + 3*self.cw + 2*self.gap + self.gap + (64 if detailed else 48)
        self.ey, self.sy, self.qy = (320, 540, 790) if detailed else (294, 410, 594)
        self.pitch = self.cw+self.gap
        self.r = 10 if detailed else 12
        self.prefix = 'detail' if detailed else 'overview'
        self.parts, self.boxes, self.gates, self.lines = [], [], [], []

    def add(self, tag, content='', **attrs):
        attrs = ' '.join(f'{k.replace("_", "-")}="{escape(str(v), quote=True)}"' for k, v in attrs.items())
        self.parts.append(f'<{tag} {attrs}>{content}</{tag}>' if content else f'<{tag} {attrs}/>')

    def text(self, x, y, lines, size=22, color='navy', weight=400, anchor='start', kind='annotation'):
        for i, line in enumerate(lines):
            self.add('text', escape(line), x=x, y=y+i*(size+7), font_size=size,
                     fill=COLORS.get(color, color), font_weight=weight, text_anchor=anchor, data_kind=kind)

    def icon(self, name, x, y, scale=1):
        self.add('use', href=f'#{self.prefix}-{name}', transform=f'translate({x} {y}) scale({scale})')

    def path(self, points, kind='lifecycle', arrow=False):
        self.lines.append((points, kind))
        d = 'M'+' L'.join(f'{x},{y}' for x, y in points)
        attrs = dict(d=d, fill='none', stroke=COLORS['blue' if kind=='evidence' else 'teal'],
                     stroke_width=2.2 if kind=='evidence' else 2.8, stroke_linejoin='round',
                     data_connector=kind, data_points=json.dumps(points, separators=(',', ':')))
        if kind=='evidence':attrs['stroke_dasharray']='7 6'
        if arrow:attrs['marker_end']=f'url(#{self.prefix}-'+('evidence' if kind=='evidence' else 'arrow')+')'
        self.add('path', **attrs)

    def gate(self, x, y, label):
        self.gates.append((x, y, self.r))
        self.parts.append(f'<g data-gate="{escape(label)}"><title>{escape(label)}; a distinct human decision</title>')
        self.add('circle', cx=x, cy=y, r=self.r, fill='white', stroke=COLORS['border'], stroke_width=1.4)
        self.icon('shield', x, y, self.r/18)
        self.parts.append('</g>')

    def transition(self, start, end, y, decisions, arrow=True):
        if not self.detailed:decisions = ('; then '.join(decisions),)
        centers = [start+(end-start)*(i+1)/(len(decisions)+1) for i in range(len(decisions))]
        cursor = start
        for center, decision in zip(centers, decisions):
            self.path([(cursor, y), (center-self.r-1.5, y)])
            self.gate(center, y, decision)
            cursor = center+self.r+1.5
        self.path([(cursor, y), (end, y)], arrow=arrow)
        return centers

    def card(self, x, cy, item, role=None, terminal=False):
        key, full, short, artifacts = item[:4]
        y=cy-self.ch/2
        width=self.cw+(12 if terminal and not self.detailed else 0)
        self.boxes.append((x, y, width, self.ch))
        self.parts.append(f'<g id="{self.prefix}-{key}" data-stage="{key}" data-box="{x},{y},{width},{self.ch}">')
        self.add('title', escape(' '.join(full)))
        self.add('rect', x=x, y=y, width=width, height=self.ch, rx=14,
                 fill='#eaf4f1' if terminal else '#ffffff', stroke='#afcec4' if terminal else COLORS['border'], stroke_width=1.6)
        if not terminal:self.icon('robot', x+self.cw/2, y+24, .75 if self.detailed else .62)
        label = full if self.detailed or terminal else short
        size = (24 if self.detailed else 20) if not terminal else (24 if self.detailed else 20)
        base = cy-(len(label)-1)*(size+7)/2+15 if not terminal else cy-(len(label)-1)*(size+7)/2+7
        self.text(x+width/2, base, label, size, 'teal' if terminal else 'navy', 700, 'middle', 'stage-label')
        if self.detailed or role:
            self.text(x+self.cw/2, y+self.ch+32, artifacts, 19 if self.detailed else 17,
                      'muted', 400, 'middle', 'artifact')
        if role:
            self.icon('human', x+self.cw/2, y-61, .75)
            self.text(x+self.cw/2, y-25, [role], 21 if self.detailed else 18, 'muted', 600, 'middle', 'role')
        self.parts.append('</g>')

    def lane(self, x, y, name, role):
        self.text(x, y, [name], 24 if self.detailed else 22, 'teal', 700)
        self.icon('human', x+9, y+34, .8)
        self.text(x+30, y+42, [role], 23 if self.detailed else 20, 'muted', 600, kind='role')

    def geometry_check(self):
        for points, kind in self.lines:
            if kind=='lifecycle':assert all(b[0]>=a[0] for a,b in zip(points,points[1:])), points
            for a,b in zip(points,points[1:]):
                assert a[0]==b[0] or a[1]==b[1], (a,b)
                for x,y,w,h in self.boxes:
                    if a[1]==b[1]:intersects=y+1<a[1]<y+h-1 and min(a[0],b[0])<x+w-1 and max(a[0],b[0])>x+1
                    else:intersects=x+1<a[0]<x+w-1 and min(a[1],b[1])<y+h-1 and max(a[1],b[1])>y+1
                    assert not intersects, (a,b,'card',x,y)
                for gx,gy,r in self.gates:
                    if a[1]==b[1]:intersects=abs(a[1]-gy)<r and min(a[0],b[0])<gx+r and max(a[0],b[0])>gx-r
                    else:intersects=abs(a[0]-gx)<r and min(a[1],b[1])<gy+r and max(a[1],b[1])>gy-r
                    assert not intersects,(a,b,'gate',gx,gy)

    def render(self):
        p=self.prefix
        self.parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="{p}-title {p}-desc">')
        self.add('title', 'AI SDLC Orchestrator — '+('detailed workflow' if self.detailed else 'workflow overview'), id=p+'-title')
        self.add('desc', 'Discovery, Business Refinement and Functional Analysis feed independent horizontal Engineering and QA tracks. Engineering proceeds through Technical Design, Implementation Planning, Development and Code Review, Engineering Verification, Security Review and Final Verification. QA proceeds through Test Strategy and Scenarios, Test Automation and QA Verification. Human approval and advancement remain separate decisions; the detailed view expands paired checkpoints. Current completed QA evidence is required before Engineering advances from Verification to Security. QA automation requires approved Design interfaces; execution binds current approved implementation and automation. Final Verification uses current Engineering outputs and QA evidence. Both tracks end at Verified, not Released. Advancement does not start work.', id=p+'-desc')
        self.add('metadata', 'Visual reference: complete-workflow-v2-r1 master-scene.svg; SHA-256 '+REFERENCE+'. Generated by docs/assets/generate_workflow.py; runtime-aligned activity overview, not a full state chart.')
        self.parts.append(f'''<defs>
<marker id="{p}-arrow" markerUnits="userSpaceOnUse" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#087e85"/></marker>
<marker id="{p}-evidence" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0L9 5L0 10" fill="none" stroke="#557da9" stroke-width="1.7"/></marker>
<g id="{p}-robot" fill="none" stroke="#586f7f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="-11" y="-7" width="22" height="17" rx="4"/><path d="M0 -7V-13M-14 -2V5M14 -2V5M-5 6H5"/><circle cy="-15" r="2"/><circle cx="-5" r="1.2"/><circle cx="5" r="1.2"/></g>
<g id="{p}-human" fill="none" stroke="#586f7f" stroke-width="1.8" stroke-linecap="round"><circle cy="-7" r="5"/><path d="M-10 12V8C-10 0 10 0 10 8V12"/></g>
<g id="{p}-shield" fill="none" stroke="#586f7f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M0 -13L11 -9V0C11 7 5 12 0 15C-5 12 -11 7 -11 0V-9Z"/><path d="M-4 7V-3H4V7M-7 7H7"/></g>
</defs>''')
        self.add('rect', width=self.w, height=self.h, fill=COLORS['background'])
        self.parts.append('<g font-family="Arial, Helvetica, sans-serif">')
        self.text(self.margin, 25, ['AI SDLC ORCHESTRATOR'], 18 if self.detailed else 15, 'teal', 700)
        self.text(self.margin, 82 if self.detailed else 72, ['From idea to verified delivery'], 42 if self.detailed else 32, weight=700)
        self.text(self.margin, 124 if self.detailed else 108, ['One shared path. Two independently governed work tracks.'], 25 if self.detailed else 21, 'muted')
        self.text(self.sx, self.sy-self.ch/2-102, ['SHARED SDLC PATH'], 24 if self.detailed else 22, 'teal', 700)
        self.lane(self.ex, self.ey-self.ch/2-94, 'ENGINEERING', 'Engineering Lead')
        self.lane(self.ex, self.qy-self.ch/2-94, 'QA', 'QA Lead / Tester')
        for i,item in enumerate(SHARED):
            x=self.sx+i*self.pitch
            self.card(x,self.sy,item,role=item[4])
            if i<2:self.transition(x+self.cw,x+self.pitch,self.sy,SHARED_GATES[i])
        last=self.sx+2*self.pitch+self.cw
        branch=self.ex-(32 if not self.detailed else 40)
        self.transition(last,branch,self.sy,SHARED_GATES[2],arrow=False)
        self.path([(branch,self.sy),(branch,self.ey),(self.ex,self.ey)],arrow=True)
        self.path([(branch,self.sy),(branch,self.qy),(self.ex,self.qy)],arrow=True)
        eng_terminal=self.ex+6*self.pitch
        join=None
        for i,item in enumerate(ENGINEERING):
            x=self.ex+i*self.pitch
            self.card(x,self.ey,item)
            centers=self.transition(x+self.cw,x+self.pitch,self.ey,ENGINEERING_GATES[i])
            if item[0]=='verification':join=centers[0]
        self.card(eng_terminal,self.ey,('engineering-verified',('Engineering','Verified'),(),()),terminal=True)
        qa_terminal=self.ex+3*self.pitch
        for i,item in enumerate(QA):
            x=self.ex+i*self.pitch
            self.card(x,self.qy,item)
            end=x+self.pitch if i<2 else qa_terminal
            self.transition(x+self.cw,end,self.qy,QA_GATES[i])
        self.card(qa_terminal,self.qy,('qa-verified',('QA','Verified'),(),()),terminal=True)
        terminal_width=self.cw+(12 if not self.detailed else 0)
        self.path([(qa_terminal+terminal_width,self.qy),(join,self.qy),
                   (join,self.ey+self.r+2)],'evidence',True)
        self.text(join+24,(self.ey+self.qy)/2-10,['Current approved QA','results + completion'],23 if self.detailed else 20,'blue',600)
        if self.detailed:
            self.text(self.ex,self.qy+self.ch/2+126,
                      ['Automation needs approved Design interfaces; QA execution binds current approved implementation and automation.'],
                      21,'muted')
        ly=self.h-(204 if self.detailed else 164)
        self.icon('robot',self.margin+12,ly,.8)
        self.text(self.margin+36,ly+7,['AI-assisted work'],22 if self.detailed else 20,'muted')
        hx=self.margin+(320 if self.detailed else 260)
        self.icon('human',hx,ly,.8);self.text(hx+24,ly+7,['Human accountability'],22 if self.detailed else 20,'muted')
        gx=hx+(375 if self.detailed else 295)
        self.icon('shield',gx,ly,.8);self.text(gx+24,ly+7,['Human decision gate'],22 if self.detailed else 20,'muted')
        decision_note = ('Paired shields: approve the revision, then separately advance. Discovery uses explicit completion.' if self.detailed else
                         'Human checkpoints preserve separate approval and advancement. Discovery uses explicit completion.')
        self.text(self.margin,ly+58,[decision_note],23 if self.detailed else 20)
        self.text(self.margin,ly+92,['Assignment is not approval. Advancement is not starting work. Independent tracks do not automatically run parallel agents.'],22 if self.detailed else 19,'muted')
        self.text(self.w-self.margin,self.h-35,['Verified ≠ Released'],25 if self.detailed else 22,'teal',700,'end')
        if not self.detailed:self.text(self.margin,self.h-35,['Full stage names and artifacts: expanded workflow'],19,'muted')
        self.parts+=['</g>','</svg>']
        self.geometry_check()
        assert eng_terminal+self.cw<self.w-self.margin, (eng_terminal,self.w)
        return '\n'.join(self.parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    validate_runtime()
    for detailed,name in ((False,'workflow-overview.svg'),(True,'workflow-detailed.svg')):
        value=Diagram(detailed).render();path=Path(__file__).with_name(name)
        if args.check:assert path.read_text()==value, f'Regenerate {name}'
        else:path.write_text(value)
    print('Both diagrams match runtime order, artifact names and geometry'+(' and checked-in SVGs.' if args.check else '.'))


if __name__=='__main__':main()
