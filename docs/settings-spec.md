---
description: Behavior spec for the viewer's reader settings - every setting's values, defaults, storage key, scope and edge cases, the Markdown reader controls, remembered state, and known gaps with recommended fixes.
tags: [repo-pages, settings, spec, sidebar, tree, theme, text-size, alternating-rows, folder-icons, sort, localStorage]
---

# Settings spec

This spec says what a reader sees and what each setting does. Measurements, colors and exact labels are in [design.md](design.md).

Names such as `--ui-scale` and `.tree-file` are the ones in [viewer/index.html](../viewer/index.html).

## Rules for every preference

- **Save on change.** There is no Save button. Each change applies at once and is written to browser storage.
- **Validate on load.** A stored value outside the allowed list or range falls back to the default. Browser storage is untrusted, because any page on the same origin can write it.
- **Survive storage failure.** If storage is blocked, the defaults apply and the page still works.
- **One key registry.** All keys come from one constant with one prefix, `rp.`.

## Settings at a glance

Defaults are in bold. Every key uses the `rp.` prefix.

| Section | Setting | Control | Values | Key |
|---|---|---|---|---|
| Appearance | Theme | 3 options | Light, Dark, **System** | `rp.theme` |
| Appearance | Interface text | 4 options | S 90%, **M 100%**, L 110%, XL 125% | `rp.ui.scale` |
| Tree | Tree text | 4 options | S 90%, **M 100%**, L 110%, XL 125% | `rp.tree.scale` |
| Tree | Folder indentation | 3 options | Compact, **Default**, Custom | `rp.tree.indent` |
| Tree | Custom indentation | Number, shown for Custom | 0.5 to 4.0 rem, **2.0** | `rp.tree.indentCustom` |
| Tree | Row density | 3 options | Compact, **Default**, Comfortable | `rp.tree.density` |
| Tree | Sort | 2 options | **Name**, Recently updated | `rp.tree.sort` |
| Tree | Vertical guide lines | Toggle | **On**, Off | `rp.tree.guideLines` |
| Tree | Alternating row colors | Toggle | On, **Off** | `rp.tree.zebra` |
| Tree | Stripes, shown when on | 2 options | **Full row**, From indent | `rp.tree.zebraSpan` |
| Tree | Strength, shown when on | 2 options | Subtle, **Medium** | `rp.tree.zebraStrength` |
| Tree | Folder icons | Toggle | On, **Off** | `rp.tree.folderIcons` |
| Tree | Style, shown when on | 2 options | Outline, **Filled** | `rp.tree.iconStyle` |
| Tree | Color, shown when on | 2 options | Muted, **Accent** | `rp.tree.iconColor` |
| Tree | File type badges | Toggle | **On**, Off | `rp.tree.typeBadges` |
| Tree | Item counts on folders | Toggle | **On**, Off | `rp.tree.folderCounts` |
| Tree | Wrap long names | Toggle | On, **Off** | `rp.tree.wrapNames` |
| Tree | Reveal the open file | Toggle | **On**, Off | `rp.tree.reveal` |
| Lists | Start on tab | 5 options | **Folders**, New, Updated, Authors, History | `rp.nav.defaultTab` |
| Lists | New and Updated show | 4 options | **Latest**, 7d, 30d, 90d | `rp.nav.recentDays` |
| Documents | Text | Stepper | 80, 90, **100**, 110, 120, 135, 150% | `rp.md.textScale` |
| Documents | Width | 3 options | Narrow, **Normal**, Full | `rp.md.width` |
| Documents | Doc theme | 3 options | **Match**, Light, Dark | `rp.md.theme` |

## Storage

- `rp.theme` stores `"light"`, `"dark"` or `"system"`. The script in `<head>` that applies the theme before first paint accepts only `"light"` and `"dark"`, so `"system"` sets no theme attribute and the CSS follows the operating system.
- Values are stored as JSON. `rp.nav.recentDays` holds a number (`0`, `7`, `30` or `90`), and `0` means Latest. The two text scales hold `0.9`, `1`, `1.1` or `1.25`.
- Each setting has one registry entry with its storage key, validator and default. Reset reads its defaults from that registry, so a new setting is reset without extra code.
- A stored value that fails its validator gives the default. This includes values from an earlier design, such as an icon color of `"amber"`.

## Footer

The nav footer order is the gear, then the build stamp, then the light/dark button. The stamp takes the free space, so the gear sits at the left edge and the light/dark button at the right edge. The popover opens directly above the gear.

## Settings popover

The popover has four sections: Appearance, Tree, Lists and Documents. [design.md](design.md#popover-contents-top-to-bottom) lists every row in order.

| Behavior | Rule |
|---|---|
| Open | The gear toggles the popover. The gear shows its active state while the popover is open |
| Close | The × button, Esc, or a click on the part of the panel outside the popover. After Esc, focus returns to the gear |
| Focus on open | The first selected option, which is the Theme row's selected option |
| Applying a change | Each change applies at once and is saved at once. There is no Save button |
| Focus after a change | Focus stays on the pressed control, even though the body is rebuilt |
| Scroll after a change | The body keeps its scroll position. Opening the popover starts at the top |
| Sub-options | Stripes and Strength appear only while Alternating row colors is on. Style and Color appear only while Folder icons is on. Their values are kept while hidden |
| Tall content | The body scrolls once the settings are taller than the panel. The header and the Reset footer stay in place |
| Changes made elsewhere | The footer light/dark button and the doc footer controls redraw an open popover, so both show the same values |

### Reset to defaults

Reset restores every setting in the table above, including the theme and the three document settings. It does not touch open folders, sidebar width, the collapsed state, notes mode or history.

Reset does not switch the active tab. Start on tab takes effect on the next page load.

## Appearance

### Theme

- **Light or Dark** sets the interface theme and stores it.
- **System** removes the theme attribute and stores `"system"`. The interface then follows the operating system, including when the operating system changes while the page is open. The doc footer's theme buttons redraw on that change.
- **The footer button** switches to the opposite of what is on screen and stores that explicit choice. Choosing System in the popover is the way back to following the operating system.
- A document whose Doc theme is Match follows the interface theme in all of these cases.

### Interface text

One multiplier, `--ui-scale`, applies to the fixed font sizes of the interface. [design.md](design.md#type-scale) lists each element and its base size.

- **Included:** the panel header, chips, tabs, toolbar and footer; the settings popover; the two header rows, breadcrumbs and buttons; dropdown menus; the file info popover; the doc footer; the whole search palette, including its result rows and headings; type badges in the header row, menus and palette; and the toast.
- **Not included:** document content, code, CSV and JSON views, the home, folder and search pages with their type badges, and the "On this page" outline.
- **Not changed:** icon buttons, header row heights and other pixel-sized controls keep their size.

Do not change the root font size to do this. Document styles use `rem` as well, so that would scale the content too.

## Tree

### Tree text

One multiplier, `--tree-scale`, applies to everything inside the sidebar's scrolling list. That covers tree rows, count pills and type badges, and also the New, Updated, Authors and History lists.

The chevron and folder icon grow with it. So does the guide line's position, which keeps the line under the chevron at every size. See [Tree geometry](design.md#tree-geometry).

Tree text has no effect outside the sidebar's list, because the multiplier is scoped to that list. The same classes follow Interface text in menus and the palette, and keep fixed sizes on pages.

### Folder indentation

The indent per nesting level drives the tree. The vertical guide line sits at the folder row's left padding plus half the chevron width, so it runs under the chevron in every indent mode and at every Tree text size. The chevron is 13px wide at 100% tree text and grows with Tree text.

| Option | Indent per level |
|---|---|
| Compact | `1.0rem` |
| Default | `1.55rem` |
| Custom | The entered value, in `rem` |

A row's left padding is `0.85rem`, unless the indent is too small to hold it. Then the padding shrinks so that the chevron's center lands on the indent. [design.md](design.md#tree-geometry) has the formula.

- A custom entry that is not a number, or that is outside 0.5 to 4.0, is ignored while typing. A valid entry is rounded to two decimals.
- The value is applied as one CSS custom property on the root, `--tree-indent`. The CSS derives `--tree-row-px` and `--tree-line-x` from it, so the tree CSS never reads JavaScript state.
- With guide lines off, the left border of every nested list becomes transparent, and the layout does not shift.
- Each level starts exactly one indent to the right of its parent, plus the guide line's 1px border. The one exception is Custom at its 0.5rem minimum with XL tree text, where half the chevron is a fraction of a pixel wider than the indent.

### Row density

Row density sets the vertical padding of tree rows: Compact `0.1rem`, Default `0.22rem`, Comfortable `0.36rem`. It applies to tree rows only, not to the New, Updated, Authors or History lists.

### Sort

- **Name** compares names with locale rules.
- **Recently updated** puts the file with the newest last commit first. Files with the same date fall back to name order. A folder sorts by the newest file anywhere beneath it.
- Folders stay above files at every level, in both modes.
- The Previous and Next arrows, the "2 / 6" counter and the jump list follow the same order, so stepping through files matches the tree.
- Breadcrumb menus and folder pages follow the same order, using the same comparison. Changing Sort redraws an open folder page and the file counter at once.
- The home page's folder cards stay in name order, because they are a directory rather than a tree.

### Vertical guide lines

Full-row stripes paint behind the lines, so the lines stay visible on striped rows.

### Alternating row colors

Every second visible row gets a stripe, counted from the top of the list after each render.

- **Counted rows:** tree folders, tree files and the file rows in the New, Updated, Authors and History lists. Commit headers and author headers are not counted.
- **Nesting:** counting runs across all levels, so `:nth-child` cannot do this. The viewer renders no children for a closed folder, so every rendered row is visible.
- **Open and close:** the count reruns on every render, so stripes stay even as folders open and close.
- **Groups:** each commit or author header restarts the count, so every group in the lists opens on the same shade.
- **Full row:** the stripe runs the full width of the panel, under the indent and under the guide lines.
- **From indent:** the stripe starts where the row starts.
- **Priority:** a stripe is a separate layer behind its row, in both spans. Hover and the selected color add to the stripe and never replace it, so both stay visible at every strength and in both themes.

### Folder icons

An icon sits between the chevron and the folder name, and it switches between closed and open with the folder. The chevron stays. File rows shift right by the icon's width plus its gap, so badges still start where sibling folder names start.

Icons apply to tree rows only. Breadcrumb menus and folder pages keep their own folder icon.

### File type badges and item counts

Each toggle hides its element inside the sidebar's list. Badges and counts elsewhere stay, such as the header row badge and the counts in breadcrumb menus. Hiding badges moves file names left to the position the badge held. Nothing else shifts.

### Wrap long names

Tree names wrap onto more lines instead of ending in an ellipsis. Wrapped names keep a minimum width of `7em`. Without that minimum, a deep row at large text wraps one letter per line. With it, a deep row runs past the panel and scrolls sideways, as an unwrapped row does.

The New, Updated, Authors and History lists already wrap, so this setting does not change them.

### Reveal the open file

- **On:** opening a file or folder page opens the folders on its path, saves them, and scrolls the row into view. The scroll is vertical only.
- **Off:** navigation does neither. The tree stays as the reader left it.
- The Browse panel still scrolls to the selected row when it opens, in both modes.

## Lists

### Start on tab

The tab that is active when the site loads. Choosing an option does not switch tabs at that moment.

### New and Updated show

- **Latest** shows the newest 40 commits that have a matching file.
- **7d, 30d or 90d** shows every matching commit in that window, with no 40-commit limit. A commit outside the window is skipped, and the search carries on. Author dates are not always in order, so a rebased commit with an old date must not hide newer commits below it.
- The empty message for a date window reads "Nothing in the last N days for this filter." Latest keeps "Nothing here for this filter."
- Authors and History are not affected.

## Documents

These three rows edit the same values as the doc footer. Both places stay in step, and the reader's scroll position is kept when text or width changes. The behavior of each value is in [Markdown reader controls](#markdown-reader-controls).

The popover offers Match, Light and Dark directly for Doc theme. The doc footer keeps its sun and moon buttons, where picking the theme the interface already has means Match.

## Markdown reader controls

A footer at the bottom of every rendered Markdown document has three groups, separated by thin dividers.

| Group | Controls | Values | Default | Where it applies |
|---|---|---|---|---|
| **Text** | A−, the current percent, A+ | 80, 90, 100, 110, 120, 135, 150% | 100% | Full-page documents and the notes panels |
| **Width** | Narrow, Normal, Full (icon buttons with tooltips) | Narrow 720px, Normal 1600px, Full (no limit) | Normal | Full-page documents only |
| **Doc theme** | Sun, Moon | Stored as `match`, `light` or `dark` | `match` (follows the interface theme) | Every rendered document, independent of the interface theme |

- **A− and A+ are disabled at the ends** of the step list.
- **Text size is one multiplier.** Every fixed font size in the Markdown styles multiplies `--md-text-scale`.
- **Width is one attribute** on the root, `data-md-width`. Normal width is its own property, `--md-max-width: 1600px`.
- **The reader keeps their place.** Before a text or width change, the viewer finds the first block whose bottom is below the top of the view. It notes how much of that block is above the view, as a fraction. After the change, it scrolls so the same block has the same fraction above the view.
- **Focus stays on the pressed button.** Every footer on the page rebuilds to show the new value, and keyboard focus returns to the same button.
- **Phone width.** At 375px the three groups wrap to two lines, every button keeps its full size, and the page does not scroll sideways.

### "On this page" outline

A right-hand outline sits beside full-page Markdown documents and is 280px wide. It lists `h2` and `h3` headings, with `h3` indented, and highlights the section in view. It is hidden below 960px wide and follows the document theme.

## Other remembered state

These preferences are not in the Settings popover. Reset does not touch them.

| Preference | Values | Default | Notes |
|---|---|---|---|
| Sidebar collapsed | true, false | false (docked) | `[` toggles it. The viewer restores it without the slide animation |
| Sidebar width | Pixels, 200 to 550 | 300 | Drag the sidebar edge to resize. Left and Right arrow keys on the focused edge move it 20px a press, and a double-click resets it |
| Open folders | Set of folder paths | Top-level folders open on first visit | Restored on return visits |
| Notes mode | `hide`, `sidebar` | `hide` | The default for any file with paired notes |
| History | List of recently viewed files | Empty | Shown in the History tab, with "Clear history". Each stored entry is checked before use |

## Storage keys

All keys come from the `KEYS` constant in the viewer. The prefix changes in one place if the project name changes.

| Keys | Holds |
|---|---|
| `rp.theme`, `rp.ui.scale` | Appearance |
| `rp.tree.scale`, `rp.tree.indent`, `rp.tree.indentCustom`, `rp.tree.density`, `rp.tree.sort`, `rp.tree.guideLines` | Tree layout |
| `rp.tree.zebra`, `rp.tree.zebraSpan`, `rp.tree.zebraStrength` | Alternating rows |
| `rp.tree.folderIcons`, `rp.tree.iconStyle`, `rp.tree.iconColor` | Folder icons |
| `rp.tree.typeBadges`, `rp.tree.folderCounts`, `rp.tree.wrapNames`, `rp.tree.reveal` | Other tree display settings |
| `rp.nav.defaultTab`, `rp.nav.recentDays` | Lists |
| `rp.md.theme`, `rp.md.textScale`, `rp.md.width` | Documents |
| `rp.tree.open`, `rp.nav.collapsed`, `rp.nav.width`, `rp.notes.mode`, `rp.history` | Remembered state |

Browser storage is shared by origin. Project sites under one domain share an origin, so they also share these preferences. That includes every site under a single custom domain. A per-site prefix would keep them apart, and that is not built.

## Known gaps

None are open. At XL interface text, Start on tab and Row density wrap onto two lines in the default 300px panel, because their labels no longer fit on one. That is the intended fallback, and no label is clipped. Every other option row stays on one line at every size.

## Deliberately left out

These were prototyped or suggested and then rejected. Do not add them without a new decision.

| Option | Decision |
|---|---|
| Full-panel settings sheet | Rejected in favor of the popover |
| Stepper or slider for Interface text and Tree text | Rejected in favor of S, M, L, XL |
| Amber folder icon color | Rejected. Color is Muted or Accent |
| Merge `.md` and `.html` twins into one row | Rejected |
| Reduce motion setting | Rejected |
| Icon only (no chevron) | Not chosen. Folders always show the chevron |
