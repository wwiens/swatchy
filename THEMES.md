
## Core Hue-Based Groups

**Primary**
Red, Yellow, Blue
Foundation set. No derivation.

**Secondary**
Orange, Green, Purple
Mixes of primaries.

**Tertiary**
Red-Orange, Yellow-Orange, Yellow-Green, Blue-Green, Blue-Purple, Red-Purple
Used for finer hue control.


## Value & Saturation Groups

**Pastels**
High lightness, low saturation.
Examples: baby blue, blush pink, mint.

**Muted / Soft**
Lower saturation, mid value.
Examples: dusty rose, sage, slate.

**Vibrant / Bright**
High saturation, mid–high value.
Examples: pure cyan, magenta, lemon yellow.

**Neon / Fluorescent**
Extreme saturation, high luminance.
Examples: safety green, hot pink.

---

## Temperature Groups

**Warm**
Reds, oranges, yellows, warm browns.

**Cool**
Blues, greens, violets.

**Neutral**
Grays, beige, taupe, ivory, black, white.



## Functional / Design System Groups

**Earth Tones**
Browns, clay, olive, sand, rust.
Common in craft, natural, lifestyle branding.

**Skin Tones**
Peach → deep brown gradient.
Often grouped separately for portrait/illustration work.

**Grayscale**
White → black with neutral grays.

**Metallics**
Gold, silver, copper, bronze.
Often flagged as a material property, not just color.

---

## Mood / Semantic Groups


**Jewel Tones**
Emerald, sapphire, ruby, amethyst.
High depth, medium saturation.

**Vintage / Retro**
Muted warm hues, aged pastels.

**Natural / Botanical**
Greens, florals, soil tones.

**High Contrast**
Black/white + one strong accent.

---

## Practical Tagging Model for a Marker App

Use **multi-tag classification**, not single buckets.

Example per marker:

```
YR513
tags:
- warm
- pastel
- earth-tone
- muted
```

This allows:

* PASTELS view
* WARM + PASTEL intersection
* BRAND PALETTE presets
* USER-DEFINED collections later
