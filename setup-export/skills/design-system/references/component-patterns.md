# Component Patterns

Standard patterns for common UI elements. Use these exact patterns — don't invent variations.

## Card
```tsx
<div className="rounded-2xl border border-border bg-card p-6">
  {children}
</div>
```

With hover:
```tsx
<div className="rounded-2xl border border-border bg-card p-6 transition-all hover:border-primary/30 hover:shadow-sm">
  {children}
</div>
```

## Section with Overline
```tsx
<div>
  <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground mb-3">
    Section Label
  </p>
  <div className="rounded-2xl border border-border bg-card">
    {children}
  </div>
</div>
```

## Page Header
```tsx
<div className="flex items-center justify-between">
  <div>
    <h1 className="text-2xl font-semibold tracking-tight">Page Title</h1>
    <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
      Description text here.
    </p>
  </div>
  <Button>Action</Button>
</div>
```

## Tab Bar
```tsx
<div className="flex gap-0.5 rounded-xl border border-border bg-card p-1">
  {tabs.map((tab) => (
    <button
      key={tab}
      className={cn(
        "flex-1 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-all",
        activeTab === tab
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      {tab}
    </button>
  ))}
</div>
```

## Empty State
```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <Icon className="mb-3 h-8 w-8 text-muted-foreground/40" />
  <p className="text-sm text-muted-foreground/60">
    Helpful message with clear next action.
  </p>
  <Button variant="secondary" className="mt-4">
    Take Action
  </Button>
</div>
```

## Stat Card
```tsx
<div className="rounded-2xl border border-border bg-card p-4">
  <p className="text-xs text-muted-foreground">Label</p>
  <p className="mt-1 text-2xl font-semibold font-mono tracking-tight">
    {value}
  </p>
</div>
```

## List Item
```tsx
<div className="flex items-start gap-4 rounded-2xl border border-border bg-card p-4">
  <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
  <div className="flex-1">
    <p className="text-sm">{title}</p>
    <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
  </div>
  <Button variant="ghost" size="sm">Action</Button>
</div>
```

## Score Badge (monospace)
```tsx
<Badge variant={score >= 80 ? "success" : score >= 60 ? "warning" : "destructive"}>
  {score}/100
</Badge>
```

## Loading State
```tsx
<div className="flex items-center justify-center py-12">
  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
</div>
```

## Inline Loading
```tsx
<div className="flex items-center gap-2 rounded-xl bg-primary/10 px-4 py-3 text-sm text-primary">
  <Loader2 className="h-4 w-4 animate-spin" />
  Processing...
</div>
```

## Form Field
```tsx
<div className="space-y-2">
  <label className="text-sm text-muted-foreground">Field Label</label>
  <Input placeholder="Placeholder text..." />
</div>
```

## Tag/Chip List with Add
```tsx
<div className="space-y-2">
  <label className="text-sm text-muted-foreground">Label</label>
  <div className="flex flex-wrap gap-2">
    {items.map((item, i) => (
      <Badge key={i} variant="outline" className="gap-1">
        {item}
        <button onClick={() => remove(i)}>
          <X className="h-3 w-3" />
        </button>
      </Badge>
    ))}
  </div>
  <div className="flex gap-2">
    <Input
      value={newItem}
      onChange={(e) => setNewItem(e.target.value)}
      onKeyDown={(e) => e.key === "Enter" && add()}
      placeholder="Add item..."
      className="max-w-xs"
    />
    <Button variant="ghost" size="icon" onClick={add}>
      <Plus className="h-4 w-4" />
    </Button>
  </div>
</div>
```
