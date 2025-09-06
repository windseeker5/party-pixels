# Selected Wireframe Design

## Big Screen Display (1920x1080) - Instagram Story Layout

### Layout: Full Screen with Celebration Title & Overlays

```
┌────────────────────────────────────────────────────────┐
│  ✨ Happy 50th Birthday Valérie! ✨                      │  ← PERMANENT
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │     TITLE
│                                                         │     (Animated)
│                 [PHOTO/VIDEO AREA]                      │
│                                                         │
│   ┌────────────────┐            ┌──────────────┐      │
│   │ 🎵 NOW PLAYING │            │  📱 SHARE!   │      │
│   │                │            │               │      │
│   │  Summer Vibes  │            │   [QR CODE]  │      │
│   │  by Mike       │            │               │      │
│   │                │            │ party.local   │      │
│   └────────────────┘            └──────────────┘      │
│                                                         │
│                                                         │
│                                                         │
│          ┌────────────────────────────┐                │
│          │ From: Emma's iPhone 📸      │                │
│          └────────────────────────────┘                │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ ████████████░░░░░░░░░░  15 seconds                     │
│                                                         │
│ [●][○][○][○][○] Next photos                           │
└────────────────────────────────────────────────────────┘
```

## Mobile Upload Page (375x812 - iPhone size)

```
┌─────────────────┐
│  Party Wall     │
│                 │
│ ✨ Happy 50th   │
│    Birthday     │
│   Valérie! ✨   │
│                 │
│  ┌───────────┐  │
│  │           │  │
│  │  DROP     │  │
│  │  PHOTO/   │  │
│  │  VIDEO    │  │
│  │   HERE    │  │
│  │           │  │
│  │    📸     │  │
│  └───────────┘  │
│                 │
│ Your name:      │
│ [___________]   │
│                 │
│ Add a song? 🎵  │
│ [___________]   │
│                 │
│ [  SHARE IT! ]  │
│                 │
└─────────────────┘
```

## CSS Implementation for Celebration Title

### Option 1: Glamorous Hollywood Style (Selected)

```css
.celebration-title {
  position: fixed;
  top: 20px;
  width: 100%;
  text-align: center;
  font-family: 'Great Vibes', 'Dancing Script', cursive;
  font-size: 72px;
  font-weight: 400;
  background: linear-gradient(
    90deg,
    #FFD700 0%,     /* Gold */
    #FFFFFF 25%,    /* White */
    #FFD700 50%,    /* Gold */
    #FFFFFF 75%,    /* White */
    #FFD700 100%    /* Gold */
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 4s linear infinite;
  text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
  z-index: 9999;
  letter-spacing: 2px;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.sparkle {
  animation: sparkle 3s ease-in-out infinite;
  display: inline-block;
}

@keyframes sparkle {
  0%, 100% { 
    opacity: 1; 
    transform: scale(1) rotate(0deg); 
  }
  50% { 
    opacity: 0.7; 
    transform: scale(1.2) rotate(5deg); 
  }
}
```

### Alternative Styles (for reference)

#### Option 2: Elegant Script with Glow
```css
.celebration-title-elegant {
  font-family: 'Great Vibes', cursive;
  font-size: 68px;
  color: #FFD700;
  text-shadow: 
    0 0 10px rgba(255, 215, 0, 0.5),
    0 0 20px rgba(255, 215, 0, 0.3),
    0 0 40px rgba(255, 215, 0, 0.2);
  animation: gentle-glow 3s ease-in-out infinite alternate;
}

@keyframes gentle-glow {
  from { filter: brightness(1) drop-shadow(0 0 20px gold); }
  to { filter: brightness(1.1) drop-shadow(0 0 30px gold); }
}
```

#### Option 3: Bold Neon Party Style
```css
.celebration-title-neon {
  font-family: 'Bebas Neue', 'Impact', sans-serif;
  font-size: 80px;
  color: #FF1493;
  text-transform: uppercase;
  text-shadow: 
    0 0 5px #FF1493,
    0 0 10px #FF1493,
    0 0 20px #FF1493,
    0 0 40px #FF1493,
    0 0 80px #FF1493;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}
```

## Layout Measurements

### Big Screen (1920x1080):
- **Title Bar**: Height 100px, always visible
- **Photo/Video Area**: 1920x980px (full remaining space)
- **Music Overlay**: Bottom-left, 300x120px
- **QR Code**: Top-right, 150x150px
- **Attribution**: Top-left, auto-width x 40px
- **Progress Bar**: Bottom, full-width x 30px

### Mobile Upload (375x812):
- **Title**: Top 120px
- **Upload Area**: 300x200px centered
- **Form Fields**: Each 40px height
- **Button**: 60px height, full-width

## Animation Performance for RPi

All animations use hardware-accelerated CSS properties:
- `transform` (GPU accelerated)
- `opacity` (GPU accelerated)
- `filter` (limited use)
- Avoid: `width`, `height`, `left`, `top` during animations

## Color Scheme

**Primary Colors:**
- Gold: `#FFD700`
- White: `#FFFFFF`
- Deep Pink: `#FF1493` (accents)
- Black: `#000000` (backgrounds)

**Gradients:**
- Title: Gold → White → Gold shimmer
- Background overlays: `rgba(0, 0, 0, 0.7)`
- Success states: Green gradient
- Error states: Red gradient

## Typography Hierarchy

1. **Celebration Title**: Great Vibes 72px
2. **Section Headers**: Bebas Neue 24px
3. **Body Text**: Arial 16px
4. **Small Text**: Arial 14px
5. **Attribution**: Arial 14px italic

## Responsive Breakpoints

- **Large Screen** (1920x1080+): Full layout
- **Medium Screen** (1024-1919px): Scaled layout
- **Mobile** (320-768px): Upload interface only

The celebration title adapts font size:
- 1920px+: 72px
- 1024-1919px: 60px
- 768-1023px: 48px
- <768px: 36px