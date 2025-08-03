"""
SPLIT DATA POPUP WINDOW HEIGHT ADJUSTMENT
==========================================

ISSUE: Window height was too tall at 420px
SOLUTION: Reduced to optimal height while keeping buttons visible

CHANGES APPLIED:
================

HEIGHT REDUCTION:
- BEFORE: 400x420 pixels (too tall)
- AFTER:  400x380 pixels (optimal size)
- CHANGE: -40 pixels height reduction

PREVIEW TEXT OPTIMIZATION:
- BEFORE: height=5 lines (too much space)
- AFTER:  height=4 lines (sufficient for content)
- RESULT: More compact layout

OPTIMAL WINDOW LAYOUT (400x380):
================================
┌─────────────────────────────────────┐
│           Split Data into Sets      │ ← Title (20px)
├─────────────────────────────────────┤
│     Total frames: XXXX              │ ← Info (25px)
├─────────────────────────────────────┤
│  Split Ratios (%)                   │ ← Ratio Controls (90px)
│  Train:    [70] %                   │
│  Validation: [20] %                 │  
│  Test:     [10] %                   │
├─────────────────────────────────────┤
│  Preview:                           │ ← Preview (4 lines = 80px)
│  Train: XXX frames (70.0%)          │
│  Validation: XX frames (20.0%)      │
│  Test: XX frames (10.0%)            │
├─────────────────────────────────────┤
│                                     │ ← Button area (45px)
│     [  Split  ]    [ Cancel ]       │
└─────────────────────────────────────┘

BENEFITS:
=========
✅ Perfect height - not too tall, not too short
✅ All content fits comfortably
✅ Buttons clearly visible and accessible  
✅ Better proportions and visual balance
✅ More reasonable screen space usage
✅ Professional and clean appearance

WINDOW SIZE EVOLUTION:
======================
1. Original: 350x300 (buttons not visible)
2. Fixed:    400x420 (too tall)  
3. Optimal:  400x380 (perfect balance)

The popup window now has the ideal size - large enough to show all 
content including buttons, but not unnecessarily tall!
"""
