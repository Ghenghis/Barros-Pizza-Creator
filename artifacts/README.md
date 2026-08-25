# Certified plugin artifact

`Barros.PizzaCreator.AI.dll` is compiled from the checked-in `plugin-src` against the exact supplied Pizza Creator 0.11.272 assemblies. `build-provenance.json` locks the compiler, input assembly hashes, output hash, and proof boundary.

The binary is not evidence that Unity loaded it. Loader and live-feature proof is collected separately by `scripts/Invoke-ProofContract.ps1` on the Windows game installation.
