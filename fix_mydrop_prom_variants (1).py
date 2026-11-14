#!/usr/bin/env python3
"""Fix mixed variant 'Стан/Состояние' attributes in MyDrop YML for Prom.ua.

Run AFTER SEO generation: python fix_mydrop_prom_variants.py public/mydrop.xml
The product's 'нюанс' warning remains in title, size and descriptions.
"""
import argparse
import os
from collections import defaultdict
from pathlib import Path
from lxml import etree

STATE_NAMES = {'стан', 'состояние'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xml', nargs='?', default='public/mydrop.xml')
    args = ap.parse_args()
    path = Path(args.xml)
    tree = etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True))
    offers = tree.findall('.//offer')
    groups = defaultdict(list)
    for offer in offers:
        gid = offer.get('group_id')
        if gid:
            groups[gid].append(offer)

    changes = []
    for gid, members in groups.items():
        with_state = [o for o in members if any((p.get('name') or '').strip().casefold() in STATE_NAMES for p in o.findall('param'))]
        if not with_state or len(with_state) == len(members):
            continue
        for offer in with_state:
            # Only remove the conflicting extra variant parameter; do not erase defect disclosure.
            title = ' '.join(filter(None, [offer.findtext('name'), offer.findtext('name_ua')])).casefold()
            desc = ' '.join(filter(None, [offer.findtext('description'), offer.findtext('description_ua')])).casefold()
            sizes = ' '.join((p.text or '') for p in offer.findall('param') if (p.get('name') or '').casefold() in {'розмір', 'размер'}).casefold()
            if 'нюанс' not in (title + ' ' + desc + ' ' + sizes):
                raise ValueError(f"Refusing to remove state from offer {offer.get('id')}: nuance not disclosed")
            for p in list(offer.findall('param')):
                if (p.get('name') or '').strip().casefold() in STATE_NAMES:
                    changes.append((offer.get('id'), gid, p.text))
                    offer.remove(p)

    # Check all groups have consistent presence of state param.
    for gid, members in groups.items():
        flags = [any((p.get('name') or '').strip().casefold() in STATE_NAMES for p in o.findall('param')) for o in members]
        if len(set(flags)) > 1:
            raise AssertionError(f'Mixed state param still exists in group {gid}')

    tmp = path.with_name(path.name + '.fix.tmp')
    try:
        tree.write(str(tmp), encoding='UTF-8', xml_declaration=True, pretty_print=True)
        etree.parse(str(tmp), etree.XMLParser(resolve_entities=False, no_network=True))
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(f'Checked {len(offers)} offers and {len(groups)} variant groups; fixed {len(changes)} offers')
    for offer_id, gid, value in changes:
        print(f'  offer={offer_id}, group={gid}, previous state={value}')

if __name__ == '__main__':
    main()
