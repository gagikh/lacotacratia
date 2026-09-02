#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Լակոտակրատիա — շապիկի (draft-note) ցուցանիշների ավտոմատ վերահաշվարկ։

Գործարկել ամեն շաբաթական թարմացումից ՀԵՏՈ, տեխնիկական ստուգումից ԱՌԱՋ.
    python3 tools/update-masthead.py            # թարմացնում է index.html-ը
    python3 tools/update-masthead.py --check    # միայն ցույց է տալիս թվերը
Տարբերակի համարը բարձրացնելու համար՝ --version 0.9
"""
import re, sys, datetime, argparse

SITE = 'gagikh.github.io/lacotacratia'

def counts(h):
    chapters = len(re.findall(r'<h2[^>]*>\s*Գլուխ\s+\d+', h))
    apps     = len(re.findall(r'<h3 id="hav-[^"]+"', h))
    figs     = len(re.findall(r'<figcaption', h))
    links    = [u for u in re.findall(r'href="(https?://[^"]+)"', h) if SITE not in u]
    uniq     = len(set(links))
    notes    = len(re.findall(r'id="g\d+-src\d+"', h))
    a, b     = h.index('id="hav-a"'), h.index('id="hav-b"')
    rows_a   = len(re.findall(r'<tr><td>', h[a:b]))
    yellow   = len(re.findall(r'class="needs-source"', h))
    return dict(chapters=chapters, apps=apps, figs=figs, links=len(links),
                uniq=uniq, notes=notes, rows_a=rows_a, yellow=yellow)

def build_note(c, version, date):
    return (
        f'<p class="draft-note">Սևագիր, տարբերակ {version} '
        f'(վերջին շաբաթական թարմացում՝ {date})։ '
        f'{c["chapters"]} գլուխ, {c["apps"]} հավելված, {c["figs"]} գծապատկեր, '
        f'ապացուցման 4 չափանիշ (Չ1–Չ4), {c["links"]} աղբյուրի հղում '
        f'({c["uniq"]} եզակի URL), {c["notes"]} համարակալված ծանոթագրություն, '
        f'Հավելված Ա-ում՝ {c["rows_a"]} ժամանակագրական դրվագ։ '
        f'Դեղինով նշված {c["yellow"]} հատվածը դեռ աղբյուր չունի։ '
        f'Հայեցակարգը՝ <code>README.md</code>, տվյալաշարը՝ <code>nshanakumner.csv</code>։ '
        f'Թարմացվում է շաբաթական մշտադիտարկմամբ։</p>'
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default='index.html')
    ap.add_argument('--version', default=None)
    ap.add_argument('--date', default=None)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    h = open(args.file, encoding='utf-8').read()
    c = counts(h)

    m = re.search(r'<p class="draft-note">Սևագիր, տարբերակ\s*([\d.]+)\s*'
                  r'\(վերջին շաբաթական թարմացում՝\s*([\d-]+)\).*?</p>', h, re.S)
    if not m:
        sys.exit('ՍԽԱԼ. շապիկի draft-note-ը չի գտնվել')
    old_ver, old_date = m.group(1), m.group(2)
    version = args.version or old_ver
    date    = args.date or datetime.date.today().isoformat()

    print('Ընթացիկ ցուցանիշները՝')
    for k, v in c.items():
        print(f'  {k:9} = {v}')
    print(f'  տարբերակ  = {old_ver} → {version}')
    print(f'  ամսաթիվ   = {old_date} → {date}')

    if args.check:
        return
    h = h[:m.start()] + build_note(c, version, date) + h[m.end():]
    open(args.file, 'w', encoding='utf-8').write(h)
    print('\nՇապիկը թարմացվեց։')

if __name__ == '__main__':
    main()
