✔ real calendar date 2026-12-31 (1.131084ms)
✔ real calendar date 2027-01-01 (0.120708ms)
✔ real calendar date 2028-02-29 (0.058917ms)
✔ real calendar date 2000-02-29 (0.047708ms)
✔ real calendar date 0001-01-01 (0.055041ms)
✔ real calendar date 9999-12-31 (0.055084ms)
✔ reject non-calendar value "2026-02-29" (0.063917ms)
✔ reject non-calendar value "1900-02-29" (0.039833ms)
✔ reject non-calendar value "2026-04-31" (0.056042ms)
✔ reject non-calendar value "2026-00-01" (0.096083ms)
✔ reject non-calendar value "2026-13-01" (0.058667ms)
✔ reject non-calendar value "2026-01-00" (0.048875ms)
✔ reject non-calendar value "0000-01-01" (0.034875ms)
✔ reject non-calendar value "2026-1-01" (0.025417ms)
✔ reject non-calendar value "2026-01-01T12:00:00Z" (0.022541ms)
✔ reject non-calendar value " 2026-01-01" (0.045875ms)
✔ reject non-calendar value null (0.027792ms)
✔ reject non-calendar value 20261028 (0.022084ms)
✔ reject non-calendar value {} (0.026208ms)
✔ reject non-calendar value ["2027-01-01"] (0.022708ms)
✔ FR-002 / AC-002: leaving tasks alone preserves permitted absence (0.962792ms)
✔ FR-001 / AC-001: exact initial date 2026-12-31, other task stays undated (0.100375ms)
✔ FR-001 / AC-001: exact initial date 2027-01-01, other task stays undated (0.034208ms)
✔ FR-001 / AC-001: exact initial date 2028-02-29, other task stays undated (0.03175ms)
✔ returned copies cannot mutate stored or seeded state (0.051ms)
✔ repositories isolate independent fixtures (0.041292ms)
✔ invalid structural input leaves state unchanged (0.260916ms)
✔ unknown target returns controlled error without mutation (0.0855ms)
✔ past/today demonstrator boundaries are not product-policy decisions (0.078125ms)
✔ change/clear demonstrator boundaries preserve state without defining product policy (0.090291ms)
✔ invalid reference day cannot silently classify an assignment (0.060209ms)
✔ invalid or duplicate seed records fail explicitly (0.088042ms)
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 128.478875
