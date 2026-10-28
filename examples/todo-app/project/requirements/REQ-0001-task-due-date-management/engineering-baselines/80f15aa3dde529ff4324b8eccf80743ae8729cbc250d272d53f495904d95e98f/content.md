✔ real calendar date 2026-12-31 (1.129833ms)
✔ real calendar date 2027-01-01 (0.14625ms)
✔ real calendar date 2028-02-29 (0.050125ms)
✔ real calendar date 2000-02-29 (0.047292ms)
✔ real calendar date 0001-01-01 (0.052708ms)
✔ real calendar date 9999-12-31 (0.2305ms)
✔ reject non-calendar value "2026-02-29" (0.182083ms)
✔ reject non-calendar value "1900-02-29" (0.058875ms)
✔ reject non-calendar value "2026-04-31" (0.107167ms)
✔ reject non-calendar value "2026-00-01" (0.172875ms)
✔ reject non-calendar value "2026-13-01" (0.144334ms)
✔ reject non-calendar value "2026-01-00" (0.126125ms)
✔ reject non-calendar value "0000-01-01" (0.063125ms)
✔ reject non-calendar value "2026-1-01" (0.087958ms)
✔ reject non-calendar value "2026-01-01T12:00:00Z" (0.049542ms)
✔ reject non-calendar value " 2026-01-01" (0.042666ms)
✔ reject non-calendar value null (0.046459ms)
✔ reject non-calendar value 20261028 (0.032083ms)
✔ reject non-calendar value {} (0.029917ms)
✔ reject non-calendar value ["2027-01-01"] (0.024083ms)
✔ FR-002 / AC-002: leaving tasks alone preserves permitted absence (0.938791ms)
✔ FR-001 / AC-001: exact initial date 2026-12-31, other task stays undated (0.10225ms)
✔ FR-001 / AC-001: exact initial date 2027-01-01, other task stays undated (0.032292ms)
✔ FR-001 / AC-001: exact initial date 2028-02-29, other task stays undated (0.032208ms)
✔ returned copies cannot mutate stored or seeded state (0.050875ms)
✔ repositories isolate independent fixtures (0.047541ms)
✔ invalid structural input leaves state unchanged (0.233625ms)
✔ unknown target returns controlled error without mutation (0.086292ms)
✔ past/today demonstrator boundaries are not product-policy decisions (0.078125ms)
✔ change/clear demonstrator boundaries preserve state without defining product policy (0.254791ms)
✔ invalid reference day cannot silently classify an assignment (0.0775ms)
✔ invalid or duplicate seed records fail explicitly (0.121583ms)
✖ UI regression: saving one task preserves another draft and its focused input (15.293709ms)
✖ UI regression: removed assignment control moves focus to the updated task heading (4.332ms)
✖ UI regression: lost successful save response reconciles readback without another mutation (2.083917ms)
✖ UI regression: failed save and failed readback block retry with an unknown-outcome message (1.293459ms)
✖ UI regression: readback proving no save permits a manual retry and retains the draft (1.368917ms)
✖ UI regression: known successful save survives a failed subsequent refresh (1.008625ms)
ℹ tests 38
ℹ suites 0
ℹ pass 32
ℹ fail 6
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 145.981541

✖ failing tests:

test at test/unit.test.mjs:123:1
✖ UI regression: saving one task preserves another draft and its focused input (15.293709ms)
  AssertionError [ERR_ASSERTION]: Expected "actual" to be reference-equal to "expected":
  + actual - expected
  ... Skipped lines
  
    <ref *1> Element {
      children: [
        Element {
          children: [],
          disabled: false,
  ...
          type: 'date',
  +       value: ''
  -       value: '2028-02-29'
        },
        Element {
          children: [],
          disabled: false,
          listeners: {},
  ...
        listeners: {},
  +     parent: <ref *4> Element {
  +       children: [
  +         <ref *3> Element {
  +           children: [
  +             Element {
  +               children: [],
  +               disabled: false,
  +               listeners: {},
  +               parent: [Circular *3],
  +               tag: 'h2',
  +               textContent: 'First task',
  +               value: ''
  +             },
  +             Element {
  +               children: [],
  +               disabled: false,
  +               listeners: {},
  +               parent: [Circular *3],
  +               tag: 'p',
  +               textContent: 'Due date: 2027-01-01',
  +               value: ''
  +             }
  +           ],
  +           disabled: false,
  +           listeners: {},
  +           parent: [Circular *4],
  +           tag: 'li',
  +           value: ''
  +         },
  +         [Circular *2]
  +       ],
  +       disabled: false,
  +       listeners: {},
  +       parent: null,
  +       tag: 'div',
  +       value: ''
  +     },
  -     parent: null,
        tag: 'li',
        value: ''
      },
      tag: 'form',
      value: ''
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:130:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: [Element],
    expected: [Element],
    operator: 'strictEqual',
    diff: 'simple'
  }

test at test/unit.test.mjs:135:1
✖ UI regression: removed assignment control moves focus to the updated task heading (4.332ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected
  
  + null
  - <ref *1> Element {
  -   children: [],
  -   disabled: false,
  -   listeners: {},
  -   parent: <ref *2> Element {
  -     children: [
  -       [Circular *1],
  -       Element {
  -         children: [],
  -         disabled: false,
  -         listeners: {},
  -         parent: [Circular *2],
  -         tag: 'p',
  -         textContent: 'Due date: 2027-01-01',
  -         value: ''
  -       }
  -     ],
  -     disabled: false,
  -     listeners: {},
  -     parent: <ref *5> Element {
  -       children: [
  -         [Circular *2],
  -         <ref *3> Element {
  -           children: [
  -             Element {
  -               children: [],
  -               disabled: false,
  -               listeners: {},
  -               parent: [Circular *3],
  -               tag: 'h2',
  -               textContent: 'Second task',
  -               value: ''
  -             },
  -             Element {
  -               children: [],
  -               disabled: false,
  -               listeners: {},
  -               parent: [Circular *3],
  -               tag: 'p',
  -               textContent: 'No due date',
  -               value: ''
  -             },
  -             <ref *4> Element {
  -               children: [
  -                 Element {
  -                   children: [],
  -                   disabled: false,
  -                   htmlFor: 'date-task-2',
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   tag: 'label',
  -                   textContent: 'Initial due date for Second task',
  -                   value: ''
  -                 },
  -                 Element {
  -                   children: [],
  -                   disabled: false,
  -                   id: 'date-task-2',
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   required: true,
  -                   tag: 'input',
  -                   type: 'date',
  -                   value: ''
  -                 },
  -                 Element {
  -                   children: [],
  -                   disabled: false,
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   tag: 'button',
  -                   textContent: 'Assign due date',
  -                   type: 'submit',
  -                   value: ''
  -                 }
  -               ],
  -               disabled: false,
  -               listeners: {
  -                 submit: [AsyncFunction (anonymous)]
  -               },
  -               parent: [Circular *3],
  -               tag: 'form',
  -               value: ''
  -             }
  -           ],
  -           disabled: false,
  -           listeners: {},
  -           parent: [Circular *5],
  -           tag: 'li',
  -           value: ''
  -         }
  -       ],
  -       disabled: false,
  -       listeners: {},
  -       parent: null,
  -       tag: 'div',
  -       value: ''
  -     },
  -     tag: 'li',
  -     value: ''
  -   },
  -   tag: 'h2',
  -   textContent: 'First task',
  -   value: ''
  - }
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:140:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: null,
    expected: [Element],
    operator: 'strictEqual',
    diff: 'simple'
  }

test at test/unit.test.mjs:143:1
✖ UI regression: lost successful save response reconciles readback without another mutation (2.083917ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /2027-01-01/. Input:
  
  'No due date'
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:147:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: 'No due date',
    expected: /2027-01-01/,
    operator: 'match',
    diff: 'simple'
  }

test at test/unit.test.mjs:153:1
✖ UI regression: failed save and failed readback block retry with an unknown-outcome message (1.293459ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:157:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: false,
    expected: true,
    operator: 'strictEqual',
    diff: 'simple'
  }

test at test/unit.test.mjs:161:1
✖ UI regression: readback proving no save permits a manual retry and retains the draft (1.368917ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /still undated.*try again/i. Input:
  
  'Response lost'
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:168:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: 'Response lost',
    expected: /still undated.*try again/i,
    operator: 'match',
    diff: 'simple'
  }

test at test/unit.test.mjs:170:1
✖ UI regression: known successful save survives a failed subsequent refresh (1.008625ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /2027-01-01/. Input:
  
  'No due date'
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:176:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: 'No due date',
    expected: /2027-01-01/,
    operator: 'match',
    diff: 'simple'
  }
