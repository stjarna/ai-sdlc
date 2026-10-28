✔ real calendar date 2026-12-31 (2.347459ms)
✔ real calendar date 2027-01-01 (0.131166ms)
✔ real calendar date 2028-02-29 (0.052917ms)
✔ real calendar date 2000-02-29 (0.045625ms)
✔ real calendar date 0001-01-01 (0.063292ms)
✔ real calendar date 9999-12-31 (0.041833ms)
✔ reject non-calendar value "2026-02-29" (0.053625ms)
✔ reject non-calendar value "1900-02-29" (0.049625ms)
✔ reject non-calendar value "2026-04-31" (0.141417ms)
✔ reject non-calendar value "2026-00-01" (0.335917ms)
✔ reject non-calendar value "2026-13-01" (0.235417ms)
✔ reject non-calendar value "2026-01-00" (0.164917ms)
✔ reject non-calendar value "0000-01-01" (0.059958ms)
✔ reject non-calendar value "2026-1-01" (0.064417ms)
✔ reject non-calendar value "2026-01-01T12:00:00Z" (0.03075ms)
✔ reject non-calendar value " 2026-01-01" (0.06975ms)
✔ reject non-calendar value null (0.064333ms)
✔ reject non-calendar value 20261028 (0.0345ms)
✔ reject non-calendar value {} (0.044958ms)
✔ reject non-calendar value ["2027-01-01"] (0.031416ms)
✔ FR-002 / AC-002: leaving tasks alone preserves permitted absence (1.076375ms)
✔ FR-001 / AC-001: exact initial date 2026-12-31, other task stays undated (0.110541ms)
✔ FR-001 / AC-001: exact initial date 2027-01-01, other task stays undated (0.033458ms)
✔ FR-001 / AC-001: exact initial date 2028-02-29, other task stays undated (0.033541ms)
✔ returned copies cannot mutate stored or seeded state (0.056167ms)
✔ repositories isolate independent fixtures (0.044709ms)
✔ invalid structural input leaves state unchanged (0.237291ms)
✔ unknown target returns controlled error without mutation (0.089375ms)
✔ past/today demonstrator boundaries are not product-policy decisions (0.085666ms)
✔ change/clear demonstrator boundaries preserve state without defining product policy (0.087958ms)
✔ invalid reference day cannot silently classify an assignment (0.063375ms)
✔ invalid or duplicate seed records fail explicitly (0.112334ms)
✔ UI regression: saving one task preserves another draft and its focused input (10.920917ms)
✖ UI regression: removed assignment control moves focus to the updated task heading (6.056083ms)
✔ UI regression: lost successful save response reconciles readback without another mutation (2.780042ms)
✔ UI regression: failed save and failed readback block retry with an unknown-outcome message (1.166833ms)
✔ UI regression: readback proving no save permits a manual retry and retains the draft (0.809834ms)
✔ UI regression: known successful save survives a failed subsequent refresh (0.801583ms)
✔ UI regression: rejected input retains the useful server diagnostic after readback (0.887875ms)
✔ UI regression: different saved date is reported without claiming the attempted date succeeded (0.847834ms)
ℹ tests 40
ℹ suites 0
ℹ pass 39
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 148.116375

✖ failing tests:

test at test/unit.test.mjs:142:1
✖ UI regression: removed assignment control moves focus to the updated task heading (6.056083ms)
  AssertionError [ERR_ASSERTION]: Expected "actual" to be reference-equal to "expected":
  + actual - expected
  
  + Element {
  - <ref *1> Element {
      _disabled: false,
      children: [],
      listeners: {},
  +   parent: null,
  +   tag: 'body',
  -   parent: <ref *2> Element {
  -     _disabled: false,
  -     children: [
  -       [Circular *1],
  -       Element {
  -         _disabled: false,
  -         children: [],
  -         listeners: {},
  -         parent: [Circular *2],
  -         tag: 'p',
  -         textContent: 'Due date: 2027-01-01',
  -         value: ''
  -       }
  -     ],
  -     listeners: {},
  -     parent: <ref *5> Element {
  -       _disabled: false,
  -       children: [
  -         [Circular *2],
  -         <ref *3> Element {
  -           _disabled: false,
  -           children: [
  -             Element {
  -               _disabled: false,
  -               children: [],
  -               listeners: {},
  -               parent: [Circular *3],
  -               tabIndex: -1,
  -               tag: 'h2',
  -               textContent: 'Second task',
  -               value: ''
  -             },
  -             Element {
  -               _disabled: false,
  -               children: [],
  -               listeners: {},
  -               parent: [Circular *3],
  -               tag: 'p',
  -               textContent: 'No due date',
  -               value: ''
  -             },
  -             <ref *4> Element {
  -               _disabled: false,
  -               children: [
  -                 Element {
  -                   _disabled: false,
  -                   children: [],
  -                   htmlFor: 'date-task-2',
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   tag: 'label',
  -                   textContent: 'Initial due date for Second task',
  -                   value: ''
  -                 },
  -                 Element {
  -                   _disabled: false,
  -                   children: [],
  -                   id: 'date-task-2',
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   required: true,
  -                   tag: 'input',
  -                   type: 'date',
  -                   value: ''
  -                 },
  -                 Element {
  -                   _disabled: false,
  -                   children: [],
  -                   listeners: {},
  -                   parent: [Circular *4],
  -                   tag: 'button',
  -                   textContent: 'Assign due date',
  -                   type: 'submit',
  -                   value: ''
  -                 }
  -               ],
  -               listeners: {
  -                 submit: [AsyncFunction (anonymous)]
  -               },
  -               parent: [Circular *3],
  -               tag: 'form',
  -               value: ''
  -             }
  -           ],
  -           listeners: {},
  -           parent: [Circular *5],
  -           tag: 'li',
  -           value: ''
  -         }
  -       ],
  -       listeners: {},
  -       parent: null,
  -       tag: 'div',
  -       value: ''
  -     },
  -     tag: 'li',
  -     value: ''
  -   },
  -   tabIndex: -1,
  -   tag: 'h2',
  -   textContent: 'First task',
      value: ''
    }
  
      at TestContext.<anonymous> (file:///private/tmp/ai-sdlc-working-app-human-acceptance-osyuopn7/project/test/unit.test.mjs:147:10)
      at async Test.run (node:internal/test_runner/test:1208:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:831:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: [Element],
    expected: [Element],
    operator: 'strictEqual',
    diff: 'simple'
  }
