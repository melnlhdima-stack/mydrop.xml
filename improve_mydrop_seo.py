#!/usr/bin/env python3
"""Post-process public/mydrop.xml after the existing MyDrop feed generator.
Does not change IDs, pricing, availability, pictures, categories or variant groups.
"""
import argparse
import html
import re
from collections import Counter
from lxml import etree

UA_RU = {'Худи':'Худі','Штаны':'Штани','Джинсы':'Джинси','Куртка':'Куртка','Кофта':'Кофта','Футболка':'Футболка','Костюм':'Костюм','Жилетка':'Жилетка','Шорты':'Шорти','Рюкзак':'Рюкзак','Сумка':'Сумка','Кепка':'Кепка','Шапка':'Шапка','Носки':'Шкарпетки','Толстовка':'Толстовка'}
RU_UA = {v:k for k,v in UA_RU.items()}
RU_UA.update({'Худі':'Худи','Штани':'Штаны','Джинси':'Джинсы','Шорти':'Шорты','Шкарпетки':'Носки'})
COLOR_UA_RU = {'чорний':'черный','білий':'белый','сірий':'серый','синій':'синий','зелений':'зеленый','червоний':'красный','коричневий':'коричневый','бежевий':'бежевый','рожевий':'розовый','жовтий':'желтый','блакитний':'голубой','фіолетовий':'фиолетовый'}
COLOR_RU_UA = {v:k for k,v in COLOR_UA_RU.items()}
TYPES = {'Худі':('худі','худи',['кофта худі','толстовка худі'],['толстовка','кофта худи']), 'Штани':('штани','штаны',['брендові штани'],['брендовые штаны']), 'Джинси':('джинси','джинсы',['джинсові штани'],['джинсовые штаны']), 'Кофта на блискавці':('кофта на блискавці','кофта на молнии',['кофта на замку'],['кофта на замке']), 'Кофта':('кофта','кофта',[],[]), 'Куртка':('куртка','куртка',[],[]), 'Футболка':('футболка','футболка',[],[]), 'Костюм':('костюм','костюм',[],[]), 'Жилетка':('жилетка','жилетка',['жилет'],['жилет']), 'Шорти':('шорти','шорты',[],[]), 'Рюкзак':('рюкзак','рюкзак',[],[]), 'Сумка':('сумка','сумка',[],[]), 'Кепка':('кепка','кепка',[],[]), 'Шапка':('шапка','шапка',[],[]), 'Шкарпетки':('шкарпетки','носки',[],[])}
GENERIC = [('для повсякденних образів','для повседневных образов'),('для щоденного гардероба','для повседневного гардероба')]

def clean(s): return re.sub(r'\s+', ' ', html.unescape(s or '')).strip()
def add(offer, tag, val):
    el = offer.find(tag)
    if el is None: el = etree.SubElement(offer, tag)
    el.text = val

def first_word_type(offer):
    p = {x.get('name','').lower(): clean(x.text) for x in offer.findall('param')}
    kind = p.get('тип товару','')
    if kind in TYPES: return kind
    name = clean(offer.findtext('name_ua') or offer.findtext('name'))
    for k in TYPES:
        if name.lower().startswith(k.lower()+' '): return k
    return None

def get_brand(offer, kind):
    p = {x.get('name','').lower():clean(x.text) for x in offer.findall('param')}
    brand = p.get('бренд у назві','')
    if brand and brand != '-': return brand
    name = clean(offer.findtext('name_ua') or offer.findtext('name'))
    name = re.sub(r'\s*[—–-]\s*.*$', '', name)
    name = re.sub(r'\s+(?:розмір|размер)\s+\S+.*$', '', name, flags=re.I)
    if kind: name = re.sub('^'+re.escape(kind)+r'\s+', '', name, flags=re.I)
    return name[:70].strip() or 'товар'

def unique(seq):
    seen=set(); out=[]
    for s in seq:
        s=clean(s); key=s.casefold()
        if s and key not in seen: seen.add(key);out.append(s)
    return out

def transform(offer):
    params = {x.get('name','').lower():clean(x.text) for x in offer.findall('param')}
    kind = first_word_type(offer)
    if not kind: return False
    ua,ru,ua_alt,ru_alt = TYPES[kind]
    brand = get_brand(offer,kind)
    size = params.get('розмір') or params.get('размер') or ''
    color = params.get('колір') or params.get('цвет') or ''
    color_ua = COLOR_RU_UA.get(color.lower(),color)
    color_ru = COLOR_UA_RU.get(color.lower(),color)
    # Do not claim product gender, material, season, authenticity or fit without source evidence.
    # Preserve meaningful model/color words from original title, if present.
    original_ua = clean(offer.findtext('name_ua'))
    model = original_ua.split(' — ')[0]
    model = re.sub(r'\s+(?:розмір|размер)\s+.*$', '', model, flags=re.I)
    model = re.sub(r'^'+re.escape(ua)+r'\s+', '', model, flags=re.I)
    if model.lower().startswith(brand.lower()): model=model[len(brand):].strip()
    model = re.sub(r'\([^)]*\)', '', model).strip()
    if color_ua: model=re.sub(r'\b'+re.escape(color_ua)+r'\b','',model,flags=re.I).strip()
    model = clean(model)
    # Avoid duplicating brand or generic product type in model.
    if model.casefold() in ('',brand.casefold(),ua.casefold(),ru.casefold()): model=''
    def title(lang):
        typ=ua if lang=='ua' else ru
        clr=color_ua if lang=='ua' else color_ru
        sz=('розмір ' if lang=='ua' else 'размер ')+size if size else ''
        parts=[typ.capitalize(),brand,model,clr,sz]
        parts=unique(parts)
        name=clean(' '.join(parts))
        if len(name)<70:
            suffix = (ua_alt if lang=='ua' else ru_alt)
            additions = [x for x in suffix if x.casefold() not in name.casefold()]
            for x in additions:
                candidate=name+(' — ' if ' — ' not in name else ', ')+x
                if len(candidate)<=100: name=candidate
        if len(name)<70:
            for phrase in (GENERIC[0][0 if lang=='ua' else 1],GENERIC[1][0 if lang=='ua' else 1]):
                candidate=name+(' — ' if ' — ' not in name else ', ')+phrase
                if len(candidate)<=100: name=candidate;break
        # No blind cutting of model or size; relevance is more important than length.
        return name
    ua_title,ru_title=title('ua'),title('ru')
    add(offer,'name_ua',ua_title);add(offer,'name',ru_title)
    def keywords(lang):
        typ=ua if lang=='ua' else ru
        alt=ua_alt if lang=='ua' else ru_alt
        clr=color_ua if lang=='ua' else color_ru
        arr=[f'{typ} {brand}']+[f'{x} {brand}' for x in alt]
        if model: arr.extend([f'{typ} {brand} {model}',f'{brand} {model}'])
        if clr: arr.extend([f'{typ} {brand} {clr}',f'{brand} {clr} {typ}'])
        if size: arr.append(f'{typ} {brand} {size}')
        # Existing query variants can add genuinely different spellings, but no generic spam.
        old=clean(offer.findtext('keywords_ua' if lang=='ua' else 'keywords'))
        arr.extend(x.strip() for x in old.split(',') if x.strip())
        return ', '.join(unique(arr)[:12])
    add(offer,'keywords_ua',keywords('ua'));add(offer,'keywords',keywords('ru'))
    article=clean(offer.findtext('vendorCode'))
    # Only factual fields from the feed; no unverified promises or fabric claims.
    def description(lang):
        isua=lang=='ua'; name=ua_title if isua else ru_title
        pairs=[]
        if size: pairs.append(('Розмір' if isua else 'Размер',size))
        if color: pairs.append(('Колір' if isua else 'Цвет',color_ua if isua else color_ru))
        pairs.append(('Тип товару' if isua else 'Тип товара',ua if isua else ru))
        if brand: pairs.append(('Бренд у назві' if isua else 'Бренд в названии',brand))
        if article: pairs.append(('Артикул' if isua else 'Артикул',article))
        li=''.join(f'<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>' for k,v in pairs)
        intro=(f'{ua.capitalize()} {brand} — модель із представленого асортименту. Перевірте доступний розмір, колір та фотографії перед оформленням замовлення.' if isua else f'{ru.capitalize()} {brand} — модель из представленного ассортимента. Проверьте доступный размер, цвет и фотографии перед оформлением заказа.')
        heading='Характеристики' if isua else 'Характеристики'
        note=('Наявність і ціна оновлюються за даними постачальника.' if isua else 'Наличие и цена обновляются по данным поставщика.')
        return f'<h2>{html.escape(name)}</h2><p>{html.escape(intro)}</p><h3>{heading}</h3><ul>{li}</ul><p>{note}</p>'
    add(offer,'description_ua',description('ua'));add(offer,'description',description('ru'))
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('path',nargs='?',default='public/mydrop.xml');args=p.parse_args()
    parser=etree.XMLParser(resolve_entities=False,no_network=True,huge_tree=True)
    tree=etree.parse(args.path,parser)
    offers=tree.findall('.//offer');done=sum(transform(o) for o in offers)
    tree.write(args.path,encoding='UTF-8',xml_declaration=True,pretty_print=True)
    print(f'SEO processed: {done}/{len(offers)} offers; XML: {args.path}')
if __name__=='__main__': main()
