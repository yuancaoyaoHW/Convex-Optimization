#!/usr/bin/env python3
"""Extract figures from Boyd & Vandenberghe Convex Optimization PDF as PNG.

Usage:
    python extract_figures.py [--chapter N] [--figure N.M] [--dpi 300]

Figures are located by searching for "Figure N.M" caption text, then clipping
the region above the caption (bounded by the page header or previous text block).
Output: assets/figures/figN.M.png

The book has 0 raster images; all figures are vector drawings rendered crisp at any DPI.
PDF page index = printed page + 13.
"""
import pymupdf, re, os, sys

PDF = r"C:\Users\hw\Documents\凸优化\bv_cvxbook.pdf"
OUT_DIR = r"C:\Users\hw\Documents\凸优化\translation\assets\figures"

# Page is 612 x 792 (US Letter). Content margins ~x:[60,552], header at y~95-105.
PAGE_W, PAGE_H = 612, 792
HEADER_BOTTOM = 108   # y below the page header line
CONTENT_LEFT = 70
CONTENT_RIGHT = 545

def find_caption_page(doc, fig_num, chap):
    """Find the PDF page index where 'Figure {chap}.{fig_num}' caption appears."""
    needle = f"Figure {chap}.{fig_num} "
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if needle in t:
            # Verify it's a caption (not a forward reference like "in figure 2.8")
            # Captions start with "Figure" at line start
            if re.search(rf"(^|\n)\s*Figure {chap}\.{fig_num} ", t):
                return i
    return None

def extract_figure(doc, chap, fig_num, dpi=300):
    """Extract figure {chap}.{fig_num} as PNG. Returns output path or None."""
    page_idx = find_caption_page(doc, fig_num, chap)
    if page_idx is None:
        return None, "caption not found"
    page = doc[page_idx]
    
    # Find caption rect
    caption_str = f"Figure {chap}.{fig_num}"
    cap_rects = page.search_for(caption_str)
    if not cap_rects:
        return None, "caption rect not found"
    cap_rect = cap_rects[0]
    
    # Find the full caption text block (caption can span multiple lines)
    blocks = page.get_text("blocks")
    cap_block = None
    for b in blocks:
        x0, y0, x1, y1, txt, bno, btype = b
        if caption_str in txt and y0 >= cap_rect.y0 - 5:
            cap_block = (x0, y0, x1, y1)
            break
    
    if cap_block is None:
        cap_block = (cap_rect.x0, cap_rect.y0, cap_rect.x1, cap_rect.y1 + 60)
    
    cap_x0, cap_y0, cap_x1, cap_y1 = cap_block
    
    # The figure is ABOVE the caption. Find the upper boundary:
    # Look for the nearest text block above the caption (excluding figure-internal labels)
    # Default: from header to caption top
    fig_top = HEADER_BOTTOM
    
    # Look at text blocks above caption; find the highest one that's not a figure label
    # Figure labels (x1, x2, θ, etc.) are small. We want the block that's clearly body text.
    for b in blocks:
        x0, y0, x1, y1, txt, bno, btype = b
        # Skip blocks below or at caption level
        if y1 >= cap_y0 - 2:
            continue
        # Skip the page header
        if y0 < HEADER_BOTTOM:
            continue
        # Skip very short blocks (figure labels like "x1", "θ = 0.6")
        if len(txt.strip()) > 40 and y0 > HEADER_BOTTOM:
            # This is body text above the figure - figure starts below it
            if y1 > fig_top and y1 < cap_y0 - 10:
                fig_top = y1 + 2
    
    # Figure region: from fig_top to caption block bottom
    # x: use full content width (figures are often centered)
    fig_x0 = min(CONTENT_LEFT, cap_x0 - 20)
    fig_x1 = max(CONTENT_RIGHT, cap_x1 + 20)
    
    clip = pymupdf.Rect(fig_x0, fig_top, fig_x1, cap_y1 + 5)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"fig{chap}.{fig_num}.png")
    pix.save(out)
    return out, f"{pix.width}x{pix.height}"

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, default=2, help="chapter number")
    ap.add_argument("--all-chapters", action="store_true", help="extract all chapters 1-11")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()
    
    doc = pymupdf.open(PDF)
    
    if args.all_chapters:
        # Extract all figures from all chapters
        # First build inventory from caption search
        fig_re = re.compile(rf"(?:^|\n)\s*Figure (\d+)\.(\d+) ")
        inventory = {}
        for i in range(doc.page_count):
            t = doc[i].get_text()
            for m in fig_re.finditer(t):
                ch, fn = int(m.group(1)), int(m.group(2))
                if ch not in inventory:
                    inventory[ch] = []
                if fn not in inventory[ch]:
                    inventory[ch].append(fn)
        
        total = sum(len(v) for v in inventory.values())
        print(f"Found {total} figures across {len(inventory)} chapters")
        done = 0
        for ch in sorted(inventory):
            for fn in inventory[ch]:
                out, info = extract_figure(doc, ch, fn, args.dpi)
                done += 1
                status = "OK" if out else "FAIL"
                print(f"  [{done}/{total}] Fig {ch}.{fn}: {status} {info}")
        print(f"\nDone. {done} figures processed.")
    else:
        ch = args.chapter
        # Extract all figures in specified chapter
        fig_re = re.compile(rf"(?:^|\n)\s*Figure {ch}\.(\d+) ")
        figs = set()
        for i in range(doc.page_count):
            t = doc[i].get_text()
            for m in fig_re.finditer(t):
                figs.add(int(m.group(1)))
        print(f"Chapter {ch}: {len(figs)} figures")
        for fn in sorted(figs):
            out, info = extract_figure(doc, ch, fn, args.dpi)
            status = "OK" if out else "FAIL"
            print(f"  Fig {ch}.{fn}: {status} {info}")

if __name__ == "__main__":
    main()
