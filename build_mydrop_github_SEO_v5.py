"""MyDrop SEO V5: builds with V4, then refines titles, keywords and descriptions.
Requires build_mydrop_github_SEO_v4.py in repository root and lxml.
"""
import runpy
import re
import html
from pathlib import Path
from lxml import etree as ET

runpy.run_path('build_mydrop_github_SEO_v4.py', run_name='__main__')
path = Path('public/mydrop.xml')
tree = ET.parse(str(path))

BRANDS = {
    'HELLSTAR': ('Хеллстар', 'Хеллстар'),
    'Patagonia': ('Патагонія', 'Патагония'),
    'Polo Ralph Lauren': ('Поло Ральф Лорен', 'Поло Ральф Лорен'),
    'Ralph Lauren': ('Ральф Лорен', 'Ральф Лорен'),
    'Burberry': ('Берберрі', 'Берберри'),
    'Nike': ('Найк', 'Найк'), 'Adidas': ('Адідас', 'Адидас'),
    'Jordan': ('Джордан', 'Джордан'), 'Moncler': ('Монклер', 'Монклер'),
    'Stone Island': ('Стоун Айленд', 'Стоун Айленд'),
    'New Balance': ('Нью Беланс', 'Нью Баланс'),
    'Supreme': ('Супрім', 'Суприм'),
    'Chrome Hearts': ('Хром Хартс', 'Хром Хартс'),
    'The North Face': ('Норт Фейс', 'Норт Фейс'),
    'Carhartt': ('Кархарт', 'Кархарт'),
    'Maison Margiela': ('Мезон Маржела', 'Мезон Маржела'),
    'Lacoste': ('Лакост', 'Лакост'),
}
TYPE_WORDS = {
    'худі': ('худі', 'худи', ['худі', 'худи', 'кофта худі', 'толстовка'], ['худи', 'толстовка', 'кофта худи']),
    'пуховик': ('пуховик', 'пуховик', ['пуховик', 'куртка пуховик'], ['пуховик', 'куртка пуховик']),
    'куртка': ('куртка', 'куртка', ['куртка', 'верхній одяг'], ['куртка', 'верхняя одежда']),
    'сумка': ('сумка', 'сумка', ['сумка', 'сумочка'], ['сумка', 'сумочка']),
    'барсетка': ('барсетка', 'барсетка', ['барсетка', 'сумка', 'сумка через плече'], ['барсетка', 'сумка', 'сумка через плечо']),
    'рюкзак': ('рюкзак', 'рюкзак', ['рюкзак', 'наплічник'], ['рюкзак', 'ранец']),
    'футболка': ('футболка', 'футболка', ['футболка'], ['футболка']),
    'шорти': ('шорти', 'шорты', ['шорти'], ['шорты']),
    'штани': ('штани', 'штаны', ['штани', 'спортивні штани'], ['штаны', 'спортивные штаны']),
    'костюм': ('костюм', 'костюм', ['костюм', 'комплект'], ['костюм', 'комплект']),
    'кепка': ('кепка', 'кепка', ['кепка', 'бейсболка'], ['кепка', 'бейсболка']),
    'шапка': ('шапка', 'шапка', ['шапка'], ['шапка']),
    'кофта': ('кофта', 'кофта', ['кофта'], ['кофта']),
    'жилетка': ('жилетка', 'жилетка', ['жилетка', 'жилет'], ['жилетка', 'жилет']),
}

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip(' ,-–')

def find_brand(text):
    for b in sorted(BRANDS, key=len, reverse=True):
        if re.search(r'(?<!\w)' + re.escape(b) + r'(?!\w)', text, re.I):
            return b
    return ''

def get_type(offer, title):
    for p in offer.findall('param'):
        if (p.get('name') or '').casefold() == 'тип товару':
            v = (p.text or '').casefold()
            for k in TYPE_WORDS:
                if k in v: return k
    low = title.casefold()
    for k in TYPE_WORDS:
        if k in low: return k
    return ''

def get_params(offer):
    pairs=[]; seen=set()
    for p in offer.findall('param'):
        key=clean(p.get('name')); val=clean(p.text)
        if key and val and (key.casefold(), val.casefold()) not in seen:
            pairs.append((key,val)); seen.add((key.casefold(),val.casefold()))
    return pairs

def gender_from_params(params, title):
    for k,v in params:
        if k.casefold() in ('стать', 'пол', 'gender'):
            low=v.casefold()
            if 'чолов' in low or 'муж' in low: return 'm'
            if 'жін' in low or 'жен' in low: return 'f'
    low=title.casefold()
    if re.search(r'\b(?:чоловіч\w*|мужск\w*)\b',low): return 'm'
    if re.search(r'\b(?:жіноч\w*|женск\w*)\b',low): return 'f'
    return ''

def phrases(typ, brand, title, params, lang):
    t_ua,t_ru,ua_syn,ru_syn=TYPE_WORDS[typ]
    terms=ua_syn if lang=='ua' else ru_syn
    brands=[brand, BRANDS.get(brand,('',''))[0 if lang=='ua' else 1]]
    brands=[b for b in brands if b]
    gender=gender_from_params(params,title)
    feminine=typ in ('сумка','барсетка','куртка','футболка','кепка','шапка','кофта','жилетка')
    if lang=='ua':
        adj=('чоловіча' if feminine else 'чоловічий') if gender=='m' else ('жіноча' if feminine else 'жіночий') if gender=='f' else ''
        buy='купити'; price='ціна'; order='замовити'
    else:
        adj=('мужская' if feminine else 'мужской') if gender=='m' else ('женская' if feminine else 'женский') if gender=='f' else ''
        buy='купить'; price='цена'; order='заказать'
    variants=[]
    for t in terms:
        for b in brands:
            variants += [f'{t} {b}', f'{b} {t}', f'{buy} {t} {b}', f'{t} {b} {price}', f'{order} {t} {b}']
            if adj: variants += [f'{adj} {t} {b}', f'{t} {b} {adj}']
    for k,v in params:
        if k.casefold() in ('розмір','размер','колір','цвет','сезон') and len(v)<35:
            variants += [f'{terms[0]} {brand} {v}']
    unique=[]; seen=set(); length=0
    for v in variants:
        v=clean(v); key=v.casefold()
        if key in seen or len(v)<4: continue
        delta=len(v)+(2 if unique else 0)
        if length+delta>1000: break
        unique.append(v);seen.add(key);length+=delta
    return ', '.join(unique)

def title_improved(old, typ, brand, params, lang):
    ua,ru,_,_=TYPE_WORDS[typ]; label=ua if lang=='ua' else ru
    brand_cyr=BRANDS[brand][0 if lang=='ua' else 1]
    gender=gender_from_params(params,old)
    feminine=typ in ('сумка','барсетка','куртка','футболка','кепка','шапка','кофта','жилетка')
    if lang=='ua':
        adj=('Чоловіча' if feminine else 'Чоловічий') if gender=='m' else ('Жіноча' if feminine else 'Жіночий') if gender=='f' else ''
    else:
        adj=('Мужская' if feminine else 'Мужской') if gender=='m' else ('Женская' if feminine else 'Женский') if gender=='f' else ''
    # Keep original model and attributes but strip repeated type and brand tokens.
    rest=old
    for b in (brand,brand_cyr):
        rest=re.sub(r'(?<!\w)'+re.escape(b)+r'(?!\w)',' ',rest,flags=re.I)
    rest=re.sub(r'\b(?:чоловіч\w*|жіноч\w*|мужск\w*|женск\w*)\b',' ',rest,flags=re.I)
    for word in sorted(set([ua,ru]+TYPE_WORDS[typ][2]+TYPE_WORDS[typ][3]),key=len,reverse=True):
        rest=re.sub(r'(?<!\w)'+re.escape(word)+r'(?!\w)',' ',rest,flags=re.I)
    rest=clean(rest)
    core=clean(' '.join(x for x in (adj,label,brand,rest) if x))
    tail=clean(' '.join(x for x in (adj.lower(),label,brand_cyr) if x))
    if tail.casefold() not in core.casefold() and len(core)+len(tail)+1<=180:
        core=core+' '+tail
    return core[:230].rstrip(' ,-')

def new_description(title, params, code, lang, previous):
    ru=lang=='ru'; e=html.escape
    facts=''.join(f'<li><strong>{e(k)}:</strong> {e(v)}</li>' for k,v in params)
    # Preserve supplier-specific description already embedded in V4 when available.
    match=re.search(r'<h3>(?:Опис постачальника|Описание поставщика)</h3>\s*<p>(.*?)</p>',previous or '',re.I|re.S)
    supplier=match.group(1) if match else ''
    if ru:
        intro=f'{e(title)}. В описании собраны подтверждённые сведения о модели, артикуле и доступных параметрах. Выберите нужный вариант по характеристикам и фотографиям.'
        source=f'<h3>Информация поставщика</h3><p>{supplier}</p>' if supplier else ''
        return f'<h2>{e(title)}</h2><p>{intro}</p>{source}<h3>Подробные характеристики</h3><ul>{facts}</ul><h3>Подбор варианта</h3><p>Проверьте размер, цвет и другие параметры, если они указаны в карточке. Неуказанные свойства уточняйте перед заказом.</p><h3>Заказ</h3><p>Артикул для уточнения: {e(code)}. Наличие и цена обновляются по данным поставщика.</p>'
    intro=f'{e(title)}. У цьому описі зібрано підтверджені відомості про модель, артикул і доступні параметри. Оберіть потрібний варіант за характеристиками та фотографіями.'
    source=f'<h3>Інформація постачальника</h3><p>{supplier}</p>' if supplier else ''
    return f'<h2>{e(title)}</h2><p>{intro}</p>{source}<h3>Докладні характеристики</h3><ul>{facts}</ul><h3>Вибір варіанта</h3><p>Перевірте розмір, колір та інші параметри, якщо вони вказані в картці. Не зазначені властивості уточнюйте перед замовленням.</p><h3>Замовлення</h3><p>Артикул для уточнення: {e(code)}. Наявність і ціна оновлюються за даними постачальника.</p>'

updated=0
for offer in tree.findall('.//offer'):
    original=offer.findtext('name_ua') or offer.findtext('name') or ''
    typ=get_type(offer,original)
    brand=find_brand(original)
    if not typ or not brand: continue
    params=get_params(offer)
    code=offer.findtext('vendorCode') or offer.get('id','')
    for lang in ('ua','ru'):
        suffix='_ua' if lang=='ua' else ''
        name_key='name'+suffix
        title=title_improved(offer.findtext(name_key) or original,typ,brand,params,lang)
        node=offer.find(name_key)
        if node is None: node=ET.SubElement(offer,name_key)
        node.text=title
        kw=offer.find('keywords'+suffix)
        if kw is None: kw=ET.SubElement(offer,'keywords'+suffix)
        kw.text=phrases(typ,brand,title,params,lang)
        desc=offer.find('description'+suffix)
        if desc is None: desc=ET.SubElement(offer,'description'+suffix)
        desc.text=new_description(title,params,code,lang,desc.text or '')
    updated+=1

path.parent.mkdir(parents=True,exist_ok=True)
tree.write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
print(f'SEO V5 complete: {updated} branded products refined; all other offers preserved.')
