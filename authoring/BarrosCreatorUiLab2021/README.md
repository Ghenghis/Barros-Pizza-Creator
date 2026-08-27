# Barro's Creator UI Lab (Unity 2021.3.45f2)

This is a safe visual-authoring project for the Barro's Pizza Creator add-on. It is not the original Pizza Creator source project and it does not attempt to reconstruct the compiled Steam game.

## Beginner workflow

1. Open this folder from Unity Hub with **Unity 2021.3.45f2**.
2. If the scene is not already visible, choose **Barros > 1 - Build or Refresh UI Prototype**.
3. Open `Assets/BarrosLab/Scenes/BarrosCreatorUiLab.unity` and press **Play**.
4. Click the five Barro's tabs and the prototype controls. The dark left rail represents the original game area that the add-on must never cover.
5. Choose **Barros > 2 - Export Unity 2017-Compatible UI Pack**.

The export lands in `assets/ui/generated` at the repository root. The normal Barro's installer then copies it into the game's isolated `BarrosAI/assets` directory.

## Compatibility rule

The live Pizza Creator runtime is Unity **2017.3.1p4**. Unity does not support loading newer-version AssetBundles into an older Player reliably, so this 2021 project exports only neutral PNG and JSON files. Future 3D work should export FBX/OBJ plus textures here, then use a separate isolated 2017.3.1p4 project only for the final Windows AssetBundle build.

Never select either Steam installation folder as a Unity project. Never save this lab into the Steam folder.
