---
layout: default
title: The 2.5 Discovery
---

# The 2.5 Discovery

## How we found that GitHub renders emoji at 2.5 monospace columns

Every visual-width library on the internet — Python's `unicodedata`, npm's `string-width`, Go's `runewidth` — says emoji occupy **2 monospace columns**. This is the Unicode East Asian Width standard, and it's correct for terminal emulators.

It's wrong for GitHub.

## The evidence

We created precision diagnostic tests and had a human compare pixel positions in GitHub's markdown code block rendering.

### Diagnostic 3: Two emoji vs. five characters

```
📦📦|
12345|
```

On GitHub, the two pipes align **exactly**. This means:

```
2 × emoji_width = 5
emoji_width = 2.5
```

### Diagnostic 5: Two emoji + five characters vs. ten characters

```
📦📦hello|
1234567890|
```

Again, pipes align exactly:

```
(2 × 2.5) + 5 = 10 ✓
```

### Confirmation across tests

| Test | Emoji count | Expected width | Alignment |
|------|-------------|---------------|-----------|
| 2 emoji | 2 | 5.0 | ✅ perfect |
| 4 emoji | 4 | 10.0 | ✅ perfect |
| 1 emoji | 1 | 2.5 | ❌ ±0.5 off |
| 3 emoji | 3 | 7.5 | ❌ ±0.5 off |

## The math

Since spaces are exactly 1.0 columns wide, you can only pad to integer column boundaries. When emoji produce a fractional total:

- **Even count** → 2.5 × even = integer → spaces can fill the gap → ✅ perfect
- **Odd count** → 2.5 × odd = x.5 → no integer number of spaces reaches the target → ❌ impossible

This is a **mathematical impossibility**, not a fixable bug. No amount of clever padding can align a 2.5-col-wide character to an integer grid when the count is odd.

## What aifmt does about it

1. **Uses the correct width for each platform.** The `target` parameter selects a rendering profile:
   - `"terminal"` → emoji = 2.0 cols (Unicode standard)
   - `"github"` → emoji = 2.5 cols (empirically measured)

2. **Warns when perfection is impossible.** Instead of silently producing broken output, the tool emits ⚠ warnings explaining *why* and *what to do about it*.

3. **Suggests alternatives.** Use even emoji counts, remove emoji from bordered content, or use Mermaid diagrams instead of ASCII art.

## Why no one found this before

- Terminal testing works fine (emoji = 2.0, always integer)
- Most alignment tools target terminals, not web rendering
- GitHub's font metrics are complex (proportional rendering of code blocks)
- You can't discover this by reading code — you have to **look at the pixels**

This discovery was made by a human comparing screenshots. No unit test, static analysis tool, or AI could have caught it.

## Implications

If you're building any tool that generates aligned text content for GitHub README files, wiki pages, or markdown documentation:

1. **Don't trust `len()`** — it returns 1 for every emoji
2. **Don't trust Unicode EAW** — it says 2, GitHub renders 2.5
3. **Use even emoji counts** in bordered/tabular content
4. **Test on the actual rendering target** — terminal correctness ≠ GitHub correctness
