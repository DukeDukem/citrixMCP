# Skill: update-transfer-goals

## When to use
Use this skill when the user provides updated transfer goal names (division/queue renames).
Some transfer goal names in the Transfer Matrix may be outdated and need renaming.

## How it works

1. The user provides the old name and the new name (e.g., "rename CS_Hardware to CS_HARDWARE_SUPPORT").
2. You open `KnowledgeBase/TransferMatrix.md`.
3. Use find-and-replace to change **every occurrence** of the old name to the new name throughout the file.
4. Update the **Transfer Goal Name Registry** table at the bottom of the file:
   - Change the name in the "Transfer Goal" column.
   - Update the "Last Updated" column to today's date.
5. Confirm the change to the user with: how many occurrences replaced, old name, new name.

## Procedure

```
1. Read KnowledgeBase/TransferMatrix.md
2. Count occurrences of the old transfer goal name
3. Replace ALL occurrences: old_name -> new_name (use replace_all=true)
4. Update the registry table row for the old name
5. Report: "Renamed <old> to <new> in N locations. Registry updated."
```

## Batch updates

If the user provides multiple renames at once, process them one at a time sequentially.
Example user input: "rename CS_Hardware to HW_SUPPORT and CBC_Widerruf to CBC_REVOCATION"

## Important

- Never remove entries from the Transfer Matrix, only rename.
- Always update the Last Updated date in the registry.
- If the old name is not found, report it and skip.
- The file also references transfer goals in the Quick Reference section -- make sure those are updated too.
