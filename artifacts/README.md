# Plug-in artifact boundary

`Barros.PizzaCreator.AI.dll` and `build-provenance.json` record the last exact-assembly build. The packaging and installer guards compare every current `plugin-src/*.cs` hash with that provenance. If any source differs, the old binary is omitted from the package and the Windows installer performs a real local compile against the installed Creator 0.11.272 assemblies.

Run `python tools/artifact_provenance.py --json` to inspect the state. Release promotion uses `python tools/build_release.py --require-certified-artifact` and fails closed until the rebuilt binary and regenerated provenance match the current source tree.

The binary is not evidence that Unity loaded it. Loader and live-feature proof is collected separately by `scripts/Invoke-ProofContract.ps1` on the Windows game installation.
