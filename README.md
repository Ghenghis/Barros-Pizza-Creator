# Barro's Pizza Creator Chat UI

In-game chat UI for Barro's Pizza (formerly PC3 Pizza Creator). 4 chat modes + Name dialog + sidebar tab nav. Built in Unity UI Toolkit. Truth spec: `docs/mockups/`. Design: `docs/superpowers/specs/2026-08-25-barros-creator-chat-ui-design.md`. Plan: `docs/superpowers/plans/2026-08-25-barros-creator-chat-ui.md`.

## Quick start

1. Open in Unity 2022.3.20f1
2. Open `Assets/Scenes/CreatorUI.unity`
3. Press Play

## Tests

```bash
# EditMode (no Unity Editor needed)
unity -batchmode -projectPath . -runTests -testPlatform EditMode -testResults TestResults-EditMode.xml

# PlayMode
unity -batchmode -projectPath . -runTests -testPlatform PlayMode -testResults TestResults-PlayMode.xml

# Snapshots (requires Unity in graphics mode)
node tools/snapshot-runner.mjs
```

## Scope lock

PC3 / Barro's Pizza only. PC2 (Fast Food Tycoon 2) is PROHIBITED. Do not import PC2 paths, fields, or models.

## Spec + Plan

- Design: `docs/superpowers/specs/2026-08-25-barros-creator-chat-ui-design.md`
- Plan: `docs/superpowers/plans/2026-08-25-barros-creator-chat-ui.md`
- Truth proof: `docs/evidence.md`
