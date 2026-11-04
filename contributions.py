#!/usr/bin/env python3
"""Build assets/contributions.svg from the public GitHub contribution calendar.

Real data only: counts come from github.com/users/<user>/contributions.
No token or secret is needed. If the fetch fails, the existing SVG is left untouched.
Usage: contributions.py <username> [output.svg] [saved_calendar.html]
"""
import re, sys, datetime as dt, urllib.request

user = sys.argv[1] if len(sys.argv) > 1 else "AdityaSrivastavDS"
out = sys.argv[2] if len(sys.argv) > 2 else "assets/contributions.svg"
src = sys.argv[3] if len(sys.argv) > 3 else None

MID, WINE_D, BURG, WINE, ROSE, PALE, IVORY = "#10070C", "#190B12", "#451126", "#701A3D", "#C77B9B", "#E5B5C7", "#F8F0F3"
SERIF = "Georgia,'Times New Roman','Noto Serif',serif"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
LEVEL = ["#24101a", BURG, WINE, ROSE, IVORY]

def load():
    if src:
        return open(src, encoding="utf-8").read()
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

def parse(html):
    tds = re.findall(r'<td[^>]*data-date="([^"]+)"[^>]*id="([^"]+)"[^>]*data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    days = {}
    for date, cid, lvl in tds:
        m = re.match(r"\s*(\d+)", tips.get(cid, ""))
        days[dt.date.fromisoformat(date)] = (int(m.group(1)) if m else 0, int(lvl))
    return days

def build(days):
    dates = sorted(days)
    first = dates[0]
    off = (first.weekday() + 1) % 7            # Sunday = row 0
    W, H = 1200, 440
    x0, y0, pitch, cell = 62, 150, 20.8, 17
    cols = (off + len(dates) + 6) // 7
    total = sum(c for c, _ in days.values())
    active = sum(1 for c, _ in days.values() if c > 0)
    best_d = max(dates, key=lambda d: days[d][0]); best = days[best_d][0]
    run = longest = 0
    for d in dates:
        run = run + 1 if days[d][0] > 0 else 0
        longest = max(longest, run)
    wk = [0] * cols
    cells = []; months = []; last_m = None
    for i, d in enumerate(dates):
        idx = off + i; col, row = idx // 7, idx % 7
        wk[col] += days[d][0]
        x = x0 + col * pitch; y = y0 + row * pitch
        if row == 0 and d.month != last_m:
            months.append((x, d.strftime("%b"))); last_m = d.month
        c, l = days[d]
        tw = ""
        if l >= 3:
            tw = f'<animate attributeName="opacity" values="1;.55;1" dur="{2.5 + (i % 7) * .4:.1f}s" begin="-{(i % 9) * .3:.1f}s" repeatCount="indefinite"/>'
        cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="4" fill="{LEVEL[l]}">{tw}<title>{c} on {d.isoformat()}</title></rect>')
    mx = max(wk) or 1
    bars = []
    for col, v in enumerate(wk):
        h = max(2, 56 * v / mx); x = x0 + col * pitch; y = 410 - h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{h:.1f}" rx="3" fill="url(#ac-bar)"><animate attributeName="height" from="0" to="{h:.1f}" dur="1.2s" begin="{col*.03:.2f}s" fill="freeze"/><animate attributeName="y" from="410" to="{y:.1f}" dur="1.2s" begin="{col*.03:.2f}s" fill="freeze"/></rect>')
    tiles = [(f"{total:,}", "contributions in the last year"), (str(active), "active days"),
             (str(longest), "longest streak, in days"), (str(best), f"best single day, {best_d.strftime('%b %d')}")]
    tsvg = ""
    for i, (v, lab) in enumerate(tiles):
        x = 34 + i * 290
        tsvg += (f'<rect x="{x}" y="24" width="270" height="84" rx="16" fill="#1d0d15" stroke="{ROSE}" stroke-opacity=".35"/>'
                 f'<rect class="motion" x="{x}" y="24" width="270" height="84" rx="16" fill="none" stroke="{PALE}" stroke-width="2" pathLength="1" stroke-dasharray=".14 .86" stroke-linecap="round"><animate attributeName="stroke-dashoffset" from="0" to="-1" dur="{7+i}s" repeatCount="indefinite"/></rect>'
                 f'<text x="{x+20}" y="68" font-family="{SERIF}" font-size="34" font-weight="700" fill="{IVORY}">{v}</text>'
                 f'<text x="{x+20}" y="92" font-family="{SANS}" font-size="13" fill="{ROSE}">{lab}</text>')
    mlab = "".join(f'<text x="{x:.0f}" y="138" font-family="{SANS}" font-size="12" fill="{ROSE}">{m}</text>' for x, m in months)
    dlab = "".join(f'<text x="30" y="{y0 + r * pitch + 13:.0f}" font-family="{SANS}" font-size="11" fill="{ROSE}" fill-opacity=".8">{n}</text>' for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    leg = "".join(f'<rect x="{998 + i * 22}" y="320" width="17" height="17" rx="4" fill="{c}"/>' for i, c in enumerate(LEVEL))
    gw = cols * pitch
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="ac-t ac-d">
<title id="ac-t">Contribution activity</title><desc id="ac-d">{total} contributions in the last year across {active} active days, longest streak {longest} days. Data from the GitHub contribution calendar for {user}, last day shown {dates[-1].isoformat()}.</desc>
<defs><style>.still{{display:none}}@media (prefers-reduced-motion:reduce){{.motion{{display:none}}.still{{display:inline}}}}</style>
<clipPath id="ac-clip"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<linearGradient id="ac-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MID}"/><stop offset="1" stop-color="{WINE_D}"/></linearGradient>
<linearGradient id="ac-bar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{WINE}"/><stop offset="1" stop-color="{ROSE}"/></linearGradient>
<linearGradient id="ac-band" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="ac-wipe"><rect x="0" y="120" width="{W}" height="240"><animate attributeName="width" from="0" to="{W}" dur="2.4s" fill="freeze"/></rect></clipPath>
<clipPath id="ac-gridclip"><rect x="{x0-4}" y="{y0-4}" width="{gw+8:.0f}" height="{7*pitch+8:.0f}"/></clipPath></defs>
<g clip-path="url(#ac-clip)"><rect width="{W}" height="{H}" fill="url(#ac-bg)"/>
{tsvg}{mlab}{dlab}
<g clip-path="url(#ac-wipe)">{''.join(cells)}</g>
<g class="motion" clip-path="url(#ac-gridclip)"><rect x="-120" y="{y0-4}" width="120" height="{7*pitch+8:.0f}" fill="url(#ac-band)"><animate attributeName="x" values="-120;{W}" dur="6s" repeatCount="indefinite"/></rect></g>
<text x="962" y="333" font-family="{SANS}" font-size="12" fill="{ROSE}">Less</text>{leg}<text x="1114" y="333" font-family="{SANS}" font-size="12" fill="{ROSE}">More</text>
<text x="{x0}" y="368" font-family="{SANS}" font-size="12" fill="{ROSE}">Weekly total</text>
{''.join(bars)}
<text x="{W-34}" y="430" font-family="{SANS}" font-size="11" text-anchor="end" fill="{ROSE}" fill-opacity=".7">Live GitHub data, last day shown {dates[-1].isoformat()}</text>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="{ROSE}" stroke-opacity=".22"/></g></svg>'''

if __name__ == "__main__":
    try:
        days = parse(load())
        if len(days) < 300:
            raise ValueError(f"only {len(days)} days parsed")
    except Exception as e:                      # keep the previous image rather than break the profile
        print("contribution fetch failed, leaving file unchanged:", e); sys.exit(0)
    open(out, "w", encoding="utf-8").write(build(days))
    print("wrote", out, len(days), "days")
