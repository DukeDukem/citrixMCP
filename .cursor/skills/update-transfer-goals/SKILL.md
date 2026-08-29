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
Example user input: "rename CS_Hardware to HW_SUPPORT and CBC_XF_E_WIDERRUF to CBC_REVOCATION"

## When a transfer goal no longer exists

If the user says a transfer goal **no longer exists** / was removed (no replacement queue name given):

1. Mark the registry row: Status = `Inactive (no longer exists)`, Last Updated = today.
2. Remove the goal from the **Quick Reference** active-transfer list.
3. **Prefer alternate handling over dead-end routing:**
   - If the case type fits Backoffice E-Mail (mobile cancellation, Kündigungsbestätigung, Kündigungsrücknahme, SOHO mobile Kündigung, etc.), repoint matrix rows to **CBC_CARE_ALLGEMEIN** with Action **HANDLE DIRECTLY** and a note naming the former queue + KB Themen-ID / Mein o2 paths.
   - If direct handling does not apply, set Ziel-Kontakt to `Kein Transfer` and Action to handle per KB; do not transfer.
4. Add or update a **Removed transfer goals — alternate handling** section in `TransferMatrix.md` with customer self-service paths for RE replies.
5. If the user later provides a **replacement** goal name, rename/repoint those rows instead.

## Important

- Prefer rename/repoint when a replacement is given; only deactivate when the queue is gone with no successor.
- Always update the Last Updated date in the registry.
- If the old name is not found, report it and skip.
- The file also references transfer goals in the Quick Reference section -- make sure those are updated too.
