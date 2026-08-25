# Truth Proof Evidence

Every snapshot test run writes 3 artifacts per panel to `evidence/snapshots/`:

- `{timestamp}-{panel}.png` - Unity Editor screenshot of the rendered panel
- `{timestamp}-{panel}.diff.png` - pixel diff vs mockup (red = mismatch)
- (logs in `evidence/snapshots.log`)

## Latest run

See `evidence/snapshots.log` for the most recent CI summary.

## Acceptance threshold

- **Target:** >=98.0% pixel match per panel
- **Stretch:** >=99.0%
- **Hard floor:** 93% - below this the PR is blocked

## PC3 scope guard

Every commit is checked for PC2 contamination:
```bash
grep -ril "FastFood\|tycoon\|amount_oz" creator-ui/
```
Expected: no output. If `amount_oz` appears, STOP - PC2 contamination.
