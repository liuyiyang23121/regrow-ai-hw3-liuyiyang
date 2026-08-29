# ReGrow UI implementation system

Source visual truth: `design/reference-option-1.png` (1440 × 1024).

## Visual tokens

- Background: true white `#ffffff`.
- Secondary surface: cool white `#f7faf9`.
- Primary text: ink `#172033`.
- Secondary text: `#667085`.
- Divider: `#dfe7e4`.
- Brand: emerald `#009b7a`; hover `#007f66`; soft `#eaf8f4`.
- Info: `#246bfd`; warning: `#d97706`; danger: `#d04444`.
- Radius: 6px controls, 8px panels. No large floating shells.
- Shadow: only on menus/modals; main layout uses dividers.

## Typography

- UI family: Inter, PingFang SC, Microsoft YaHei, system sans-serif.
- Body: 14px / 1.5. Controls: 13px / 1.2.
- Page title: 28px / 1.2, weight 700.
- Section title: 16px / 1.3, weight 650.
- Mono: JetBrains Mono, SFMono-Regular, Consolas.

## Layout

- Desktop reference width: 1440px.
- Sidebar: 176px. Top bar: 60px.
- Main content: objective header, six-step rail, then a 1fr/280px work area.
- Main asset panel uses tabs and an open editor surface, not nested cards.
- Mobile: sidebar collapses to a bottom navigation; inspector follows the asset area.

## Component families

- `AppSidebar`: wordmark, three navigation rows, user footer.
- `TopBar`: product description, current date, help and account controls.
- `TaskHeader`: editable objective and one primary action.
- `WorkflowRail`: six deterministic node states.
- `AssetWorkspace`: asset tabs, toolbar, main artifact, validation receipt.
- `QualityInspector`: four metric rows, checklist, report action.
- `ReviewPanel`: medium/high-risk decision with approve/reject/retry.

## Icon treatment

Use Phosphor Icons Vue: regular 1.7px-equivalent stroke, 18–20px navigation,
16px inline, emerald for success and brand actions. No emoji or text glyph icons.

## Motion

- 160ms control transitions.
- Running node uses a restrained 1.4s opacity pulse.
- Respect `prefers-reduced-motion`.

