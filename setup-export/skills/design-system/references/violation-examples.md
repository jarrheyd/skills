# Design System Violation Examples

Common violations and how to fix them.

## Hardcoded Colors

### BAD
```tsx
<div className="bg-[#F5F5F5] text-[#333333]">
<div style={{ color: '#FF0000' }}>
<div className="bg-white border-gray-200">
```

### GOOD
```tsx
<div className="bg-surface text-foreground">
<div className="text-destructive">
<div className="bg-card border-border">
```

**Rule**: All colors must come from design tokens defined in `globals.css` and referenced in `DESIGN-SYSTEM.md`.

---

## Magic Spacing

### BAD
```tsx
<div className="p-[17px] mt-[23px] gap-[11px]">
<div className="p-7"> <!-- Not in standard scale -->
```

### GOOD
```tsx
<div className="p-4 mt-6 gap-3">
<div className="p-6">
```

**Rule**: Use the spacing scale: 0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64.

---

## Wrong Border Radius

### BAD
```tsx
<div className="rounded-md border border-border bg-card p-6">   <!-- Card with rounded-md -->
<div className="rounded-2xl border border-border bg-card p-1">  <!-- Tab bar with rounded-2xl -->
```

### GOOD
```tsx
<div className="rounded-2xl border border-border bg-card p-6">  <!-- Card = rounded-2xl -->
<div className="rounded-xl border border-border bg-card p-1">   <!-- Tab bar = rounded-xl -->
```

**Radius guide:**
- Cards: `rounded-2xl` (16px)
- Tab bars, insets: `rounded-xl` (12px)
- Buttons, inputs: `rounded-lg` (8px)
- Badges: `rounded-md` (6px)
- Avatars, dots: `rounded-full`

---

## Shadow Violations

### BAD
```tsx
<div className="rounded-2xl border border-border bg-card p-6 shadow-lg">
```

### GOOD
```tsx
<div className="rounded-2xl border border-border bg-card p-6">
<!-- Shadow only on hover: -->
<div className="rounded-2xl border border-border bg-card p-6 transition-all hover:shadow-sm">
```

**Rule**: No shadows on cards at rest. `shadow-sm` on hover only. Exception: floating elements (chat panel, tooltips).

---

## Typography Violations

### BAD
```tsx
<h1 className="text-[28px] font-bold">Page Title</h1>
<p className="text-[11px]">Label</p>
```

### GOOD
```tsx
<h1 className="text-2xl font-semibold tracking-tight">Page Title</h1>
<p className="text-xs text-muted-foreground">Label</p>
```

**Type scale**: text-[10px] (overline only), text-xs (12px), text-[13px] (nav), text-sm (14px), text-base (16px), text-lg (18px), text-xl (20px), text-2xl (24px), text-3xl (30px), text-4xl (36px).

---

## Dark Mode Violations

### BAD
```tsx
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">
```

### GOOD
```tsx
<div className="bg-card text-foreground">
```

**Rule**: This app is light-mode only. No `dark:` prefixes. Use semantic tokens that will adapt when dark mode is eventually added.

---

## Visual Language Mixing

### BAD
```tsx
<!-- Some cards with shadows, some with borders -->
<div className="bg-card shadow-md p-4">Card A</div>
<div className="border border-border bg-card p-4">Card B</div>
```

### GOOD
```tsx
<!-- Consistent: all cards use border, same radius, same padding -->
<div className="rounded-2xl border border-border bg-card p-6">Card A</div>
<div className="rounded-2xl border border-border bg-card p-6">Card B</div>
```

---

## Copy/Voice Violations

### BAD
```tsx
"Welcome to your amazing dashboard! 🎉"
"Oops! Something went wrong."
"ERROR: No data found"
"Please click here to proceed"
```

### GOOD
```tsx
"Your AI agent is ready."
"Something went wrong. Try again."
"No data yet."
"Get started"
```

**Rules**: No exclamation marks in UI. No emojis in labels. No "oops" or "please". Sentence case, not Title Case.
