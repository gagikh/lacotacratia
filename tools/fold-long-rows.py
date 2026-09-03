#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Լակոտակրատիա — երկար ժամանակագրական տողերի ծալում <details>-ի մեջ։

ԽՆԴԻՐԸ. Հավելված Ա-ն ժամանակագրական ինդեքս է, բայց 2026-ի ամառվա ավելացումներով
բջիջները հասան 3500+ նիշի․ 170 տողից 42-ը զբաղեցնում էր աղյուսակի բարձրության
56.6%-ը, և ինդեքսը դադարեց սկանավորելի լինել։

ԼՈՒԾՈՒՄԸ. բջջում տեսանելի է մնում առաջին՝ վերնագրային նախադասությունը, մնացածը
դրվում է <details class="more"> ծալքի տակ։ Ոչ մի տեքստ չի կորչում․ տպագրության
ժամանակ ծալքերն ինքնաբերաբար բացվում են (index.html-ի վերջի սկրիպտով)։

ԳՈՐԾԱՐԿՈՒՄ.
    python3 tools/fold-long-rows.py --check     # ցույց է տալիս՝ ինչ կծալվի
    python3 tools/fold-long-rows.py             # կիրառում է
    python3 tools/fold-long-rows.py --threshold 700
    python3 tools/fold-long-rows.py --unfold    # հետ է բերում (ծալքերը բացում)

ԱՆՎՏԱՆԳՈՒԹՅՈՒՆ.
  * Իդեմպոտենտ է — արդեն ծալված բջիջը կրկին չի ծալվում։
  * Կտրում է ՄԻԱՅՆ պիտակների խորությունը 0 լինելու կետում, ուստի HTML-ը չի կոտրվում։
  * Չի դիպչում աղբյուրների սյունակին և ամսաթվերի սյունակին։
  * Աշխատում է Հավելված Ա-ի վրա (լռելյայն)․ --appendix b|g|e|z՝ մյուսների համար։
"""
import argparse
import re
import sys

APPENDIX_BOUNDS = {
    'a': ('id="hav-a"', 'id="hav-b"'),
    'b': ('id="hav-b"', 'id="hav-g"'),
    'g': ('id="hav-g"', 'id="hav-d"'),
    'e': ('id="hav-e"', 'id="hav-z"'),
    'z': ('id="hav-z"', '</main>'),
}
SUMMARY_LABEL = 'ամբողջական դրվագը'


def depth_zero_positions(html):
    """Վերադարձնում է այն ինդեքսների բազմությունը, որտեղ պիտակի խորությունը 0 է
    (այսինքն՝ կետը ոչ մի <tag> ... </tag> զույգի ներսում չէ և ոչ էլ պիտակի մեջտեղում)։"""
    depth, inside_tag, ok = 0, False, set()
    for i, ch in enumerate(html):
        if ch == '<':
            inside_tag = True
            closing = html[i + 1:i + 2] == '/'
            if not closing:
                pass  # խորությունը կավելանա պիտակի փակվելիս
        elif ch == '>':
            inside_tag = False
            # պարզում ենք՝ բացվող, փակվող, թե ինքնափակվող
            start = html.rfind('<', 0, i)
            tag = html[start:i + 1]
            if tag.startswith('</'):
                depth -= 1
            elif not tag.endswith('/>'):
                depth += 1
            if depth == 0:
                ok.add(i + 1)
        elif not inside_tag and depth == 0:
            ok.add(i)
    ok.add(len(html))
    return ok


# Հայերեն տեքստում նախադասությունը կարող է ավարտվել՝
#   ։ U+0589 (վերջակետ), ․ U+2024 (միջակետ, գրքում լայնորեն օգտագործվում է),
#   . ASCII կետ, ինչպես նաև ! ?
# U+2024-ի բացակայությունը regex-ից պատճառ էր, որ 7 տող չբաժանվի (02.09.2026)։
SENTENCE_END = '[։․.!?]'
MIN_HEAD = 40      # տեսանելի մասի նվազագույն երկարությունը
MIN_TAIL = 200     # ծալվող մասի նվազագույն երկարությունը
FALLBACK_MAX = 260  # ետդարձի դեպքում՝ տեսանելի մասի առավելագույնը


def split_cell(cell):
    """Բջիջը բաժանում է (տեսանելի_մաս, ծալվող_մաս)։ None՝ եթե բաժանելի չէ։"""
    ok = depth_zero_positions(cell)

    # 1-ին տարբերակ. բջիջը սկսվում է <strong>Վերնագիր։</strong> — կտրում ենք դրանից հետո
    m = re.match(r'\s*<strong>.*?</strong>', cell, re.S)
    if m and m.end() in ok and len(cell) - m.end() > MIN_TAIL:
        return cell[:m.end()], cell[m.end():].lstrip()

    # 2-րդ տարբերակ. առաջին նախադասությունը՝ խորություն 0-ում
    for m in re.finditer(SENTENCE_END + r'\s', cell):
        pos = m.end()
        if pos in ok and MIN_HEAD < pos and len(cell) - pos > MIN_TAIL:
            return cell[:pos].rstrip(), cell[pos:].lstrip()

    # 3-րդ տարբերակ (ետդարձ). ստորակետ/միջակետ խորություն 0-ում՝ FALLBACK_MAX-ի սահմաններում
    for m in re.finditer(r'[,;:—]\s', cell[:FALLBACK_MAX]):
        pos = m.end()
        if pos in ok and MIN_HEAD < pos and len(cell) - pos > MIN_TAIL:
            return cell[:pos].rstrip() + ' …', cell[pos:].lstrip()

    # 4-րդ տարբերակ. բառի սահման խորություն 0-ում
    cand = [m.end() for m in re.finditer(r'\s', cell[:FALLBACK_MAX])
            if m.end() in ok and MIN_HEAD < m.end()]
    if cand and len(cell) - cand[-1] > MIN_TAIL:
        pos = cand[-1]
        return cell[:pos].rstrip() + ' …', cell[pos:].lstrip()
    return None


def process(html, bounds, threshold, unfold=False, check=False):
    start, stop = bounds
    a = html.index(start)
    b = html.index(stop, a)
    section = html[a:b]
    report, changed = [], 0

    def handle(match):
        nonlocal changed
        date_cell, body, tail = match.group(1), match.group(2), match.group(3)

        if unfold:
            if 'details class="more"' not in body:
                return match.group(0)
            new = re.sub(r'<details class="more"><summary>[^<]*</summary>'
                         r'<span class="fold-body">(.*?)</span></details>',
                         r' \1', body, flags=re.S)
            changed += 1
            return f'<tr><td>{date_cell}</td><td>{new}</td>{tail}'

        if 'details class="more"' in body or len(body) < threshold:
            return match.group(0)
        parts = split_cell(body)
        if not parts:
            report.append(('ՉԲԱԺԱՆՎԵՑ', date_cell, len(body)))
            return match.group(0)
        head, rest = parts
        report.append(('ծալվեց', date_cell, len(body)))
        changed += 1
        if check:
            return match.group(0)
        folded = (f'{head} <details class="more"><summary>{SUMMARY_LABEL}</summary>'
                  f'<span class="fold-body">{rest}</span></details>')
        return f'<tr><td>{date_cell}</td><td>{folded}</td>{tail}'

    pattern = re.compile(r'<tr><td>([^<]*)</td><td>(.*?)</td>(<td>.*?</td></tr>)', re.S)
    new_section = pattern.sub(handle, section)

    for kind, date, n in report:
        print(f'  {kind:12} {date[:44]:46} {n:5} նիշ')
    print(f'\n{"Կծալվեր" if check else "Փոխվեց"}՝ {changed} տող '
          f'(շեմը՝ {threshold} նիշ)')
    return html[:a] + new_section + html[b:], changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default='index.html')
    ap.add_argument('--appendix', default='a', choices=sorted(APPENDIX_BOUNDS))
    ap.add_argument('--threshold', type=int, default=900,
                    help='բջջի նիշերի շեմը, որից հետո ծալվում է (լռելյայն՝ 900)')
    ap.add_argument('--check', action='store_true', help='միայն ցույց տալ')
    ap.add_argument('--unfold', action='store_true', help='հետ բերել ծալքերը')
    args = ap.parse_args()

    html = open(args.file, encoding='utf-8').read()
    new, changed = process(html, APPENDIX_BOUNDS[args.appendix],
                           args.threshold, args.unfold, args.check)
    if args.check or not changed:
        return 0
    open(args.file, 'w', encoding='utf-8').write(new)
    print(f'{args.file} գրվեց։ Հաջորդ քայլը՝ python3 tools/check-html.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
