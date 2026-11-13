"""MyDrop -> Prom SEO V6. Run V4 pricing/stock builder first; improve SEO only.
Requires build_mydrop_github_SEO_v4.py in repo root and lxml.
"""
import runpy
import re
import html
from pathlib import Path
from lxml import etree as ET

runpy.run_path('build_mydrop_github_SEO_v4.py', run_name='__main__')
path = Path('public/mydrop.xml')
tree = ET.parse(str(path))

# Source V4 already supplies category-aware types, margins, IDs, stock and images.
BRANDS = {
    'Polo Ralph Lauren': ('Поло Ральф Лорен', 'Поло Ральф Лорен'),
    'Ralph Lauren': ('Ральф Лорен', 'Ральф Лорен'),
    'New Balance': ('Нью Беланс', 'Нью Баланс'),
    'The North Face': ('Норт Фейс', 'Норт Фейс'),
    'Stone Island': ('Стоун Айленд', 'Стоун Айленд'),
    'Chrome Hearts': ('Хром Хартс', 'Хром Хартс'),
    'Maison Margiela': ('Мезон Маржела', 'Мезон Маржела'),
    'Palm Angels': ('Палм Енджелс', 'Палм Энджелс'),
    'Tommy Hilfiger': ('Томмі Гілфігер', 'Томми Хилфигер'),
    'Under Armour': ('Андер Армор', 'Андер Армор'),
    'Calvin Klein': ('Келвін Кляйн', 'Кельвин Кляйн'),
    'Loro Piana': ('Лоро Піана', 'Лоро Пиана'),
    'HELLSTAR': ('Хеллстар', 'Хеллстар'),
    'Patagonia': ('Патагонія', 'Патагония'),
    'Burberry': ('Берберрі', 'Берберри'),
    'Nike': ('Найк', 'Найк'), 'Adidas': ('Адідас', 'Адидас'),
    'Jordan': ('Джордан', 'Джордан'), 'Moncler': ('Монклер', 'Монклер'),
    'Supreme': ('Супрім', 'Суприм'), 'Carhartt': ('Кархарт', 'Кархарт'),
    'Lacoste': ('Лакост', 'Лакост'), 'Puma': ('Пума', 'Пума'),
    'Gucci': ('Гуччі', 'Гуччи'), 'Prada': ('Прада', 'Прада'),
    'Dior': ('Діор', 'Диор'), 'Balenciaga': ('Баленсіага', 'Баленсиага'),
    'Louis Vuitton': ('Луї Віттон', 'Луи Виттон'),
    'Off-White': ('Офф Вайт', 'Офф Вайт'),
    'Essentials': ('Ессеншіалс', 'Эссеншиалс'),
    'Fear of God': ('Фір оф Год', 'Фир оф Год'),
    'Armani Exchange': ('Армані Ексчендж', 'Армани Эксчендж'),
}
TYPE_DATA = {
    'худі': ('Худі', 'Худи', ['худі', 'кофта худі', 'толстовка худі'], ['худи', 'толстовка', 'кофта худи']),
    'пуховик': ('Пуховик', 'Пуховик', ['пуховик', 'куртка пуховик'], ['пуховик', 'куртка пуховик']),
    'куртка': ('Куртка', 'Куртка', ['куртка'], ['куртка']),
    'вітровка': ('Вітровка', 'Ветровка', ['вітровка', 'легка куртка'], ['ветровка', 'легкая куртка']),
    'олімпійка': ('Олімпійка', 'Олимпийка', ['олімпійка', 'спортивна кофта'], ['олимпийка', 'спортивная кофта']),
    'костюм': ('Костюм', 'Костюм', ['костюм', 'комплект одягу'], ['костюм', 'комплект одежды']),
    'шапка': ('Шапка', 'Шапка', ['шапка'], ['шапка']),
    'панама': ('Панама', 'Панама', ['панама'], ['панама']),
    'футболка': ('Футболка', 'Футболка', ['футболка'], ['футболка']),
    'шорти': ('Шорти', 'Шорты', ['шорти'], ['шорты']),
    'майка': ('Майка', 'Майка', ['майка'], ['майка']),
    'сукня': ('Сукня', 'Платье', ['сукня'], ['платье']),
    'зіпка': ('Кофта на блискавці', 'Кофта на молнии', ['зіпка', 'кофта на блискавці'], ['зипка', 'кофта на молнии']),
    'кофта': ('Кофта', 'Кофта', ['кофта'], ['кофта']),
    'светр': ('Светр', 'Свитер', ['светр'], ['свитер']),
    'світшот': ('Світшот', 'Свитшот', ['світшот'], ['свитшот']),
    'штани': ('Штани', 'Штаны', ['штани'], ['штаны']),
    'джинси': ('Джинси', 'Джинсы', ['джинси'], ['джинсы']),
    'жилетка': ('Жилетка', 'Жилетка', ['жилетка', 'жилет'], ['жилетка', 'жилет']),
    'сумка': ('Сумка', 'Сумка', ['сумка'], ['сумка']),
    'барсетка': ('Барсетка', 'Барсетка', ['барсетка', 'сумка через плече'], ['барсетка', 'сумка через плечо']),
    'рюкзак': ('Рюкзак', 'Рюкзак', ['рюкзак'], ['рюкзак']),
    'кепка': ('Кепка', 'Кепка', ['кепка', 'бейсболка'], ['кепка', 'бейсболка']),
    'гаманець': ('Гаманець', 'Кошелек', ['гаманець'], ['кошелек']),
    'ремінь': ('Ремінь', 'Ремень', ['ремінь'], ['ремень']),
    'шкарпетки': ('Шкарпетки', 'Носки', ['шкарпетки'], ['носки']),
    'аксесуар': ('Аксесуар', 'Аксессуар', ['аксесуар'], ['аксессуар']),
}
TYPE_ALIASES = {
    'худи':'худі', 'толстовка':'худі', 'ветровка':'вітровка', 'олимпийка':'олімпійка',
    'шорты':'шорти', 'штаны':'штани', 'свитер':'светр', 'свитшот':'світшот',
    'платье':'сукня', 'кошелек':'гаманець', 'ремень':'ремінь', 'носки':'шкарпетки',
    'зипка':'зіпка', 'кофта на молнии':'зіпка',
}
FEMININE = {'куртка','вітровка','олімпійка','шапка','панама','футболка','майка','сукня','кофта','жилетка','сумка','барсетка','кепка','зіпка'}
PLURAL = {'штани','джинси','шорти','шкарпетки'}
FIELD_ALIASES = {
    'тип товару': 'Тип товару', 'тип': 'Тип товару', 'вид товару': 'Тип товару',
    'розмір': 'Розмір', 'размер': 'Розмір', 'size': 'Розмір',
    'колір': 'Колір', 'цвет': 'Колір', 'color': 'Колір',
    'сезон': 'Сезон', 'season': 'Сезон',
    'стать': 'Стать', 'пол': 'Стать', 'gender': 'Стать',
    'матеріал': 'Матеріал', 'материал': 'Матеріал', 'material': 'Матеріал',
    'склад': 'Склад', 'состав': 'Склад',
    'модель': 'Модель', 'model': 'Модель',
    'артикул': 'Артикул', 'код товару': 'Артикул',
}
COLOR_MAP = {
    'чорний': ('чорний','черный'), 'черный': ('чорний','черный'), 'чёрный': ('чорний','черный'),
    'білий': ('білий','белый'), 'белый': ('білий','белый'),
    'сірий': ('сірий','серый'), 'серый': ('сірий','серый'),
    'синій': ('синій','синий'), 'синий': ('синій','синий'),
    'зелений': ('зелений','зеленый'), 'зеленый': ('зелений','зеленый'),
    'коричневий': ('коричневий','коричневый'), 'коричневый': ('коричневий','коричневый'),
    'рожевий': ('рожевий','розовый'), 'розовый': ('рожевий','розовый'),
}

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(str(s or ''))).strip(' ,;–-')

def get_node(offer, tag):
    node = offer.find(tag)
    if node is None: node = ET.SubElement(offer, tag)
    return node

def get_params(offer):
    pairs=[]; seen=set()
    for p in offer.findall('param'):
        k=clean(p.get('name')); v=clean(p.text)
        if not k or not v or len(v)>200: continue
        canonical=FIELD_ALIASES.get(k.casefold(),k)
        key=(canonical.casefold(),v.casefold())
        if key not in seen:
            seen.add(key);pairs.append((canonical,v))
    return pairs

def param(params, key):
    return next((v for k,v in params if k.casefold()==key.casefold()), '')

def detect_brand(title, params):
    # Brand can be mentioned in supplier title; not proof of authenticity.
    text=title+' '+param(params,'Бренд у назві')
    for brand in sorted(BRANDS,key=len,reverse=True):
        if re.search(r'(?<!\w)'+re.escape(brand)+r'(?!\w)',text,re.I): return brand
    return ''

def detect_type(title, params):
    p=param(params,'Тип товару').casefold()
    for key in TYPE_DATA:
        if key in p: return key
    for alias,key in TYPE_ALIASES.items():
        if alias in p: return key
    t=title.casefold()
    for key in sorted(TYPE_DATA,key=len,reverse=True):
        if re.search(r'(?<!\w)'+re.escape(key)+r'(?!\w)',t): return key
    for alias,key in TYPE_ALIASES.items():
        if re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',t): return key
    return ''

def detect_gender(title,params):
    t=(param(params,'Стать')+' '+title).casefold()
    if re.search(r'чоловіч\w*|мужск\w*|\bmen\b|\bmens\b',t): return 'm'
    if re.search(r'жіноч\w*|женск\w*|\bwomen\b|\bwomens\b',t): return 'f'
    return ''

def gender_label(typ,gender,lang):
    if not gender: return ''
    if typ in PLURAL:
        return ('Чоловічі' if gender=='m' else 'Жіночі') if lang=='ua' else ('Мужские' if gender=='m' else 'Женские')
    if typ in FEMININE:
        return ('Чоловіча' if gender=='m' else 'Жіноча') if lang=='ua' else ('Мужская' if gender=='m' else 'Женская')
    return ('Чоловічий' if gender=='m' else 'Жіночий') if lang=='ua' else ('Мужской' if gender=='m' else 'Женский')

def color_value(value,lang):
    if not value: return ''
    return COLOR_MAP.get(value.casefold(),(value,value))[0 if lang=='ua' else 1]

def source_model(offer,params,brand,typ):
    # Extract only actual supplier model, not SEO title generated by V4.
    explicit=param(params,'Модель')
    if explicit: return explicit
    # V4 title may contain an original model token; use only distinctive Latin/digit identifiers.
    title=offer.findtext('name_ua') or offer.findtext('name') or ''
    tokens=re.findall(r'(?<!\w)[A-Za-z][A-Za-z0-9-]{2,}(?!\w)',title)
    blacklist=set(re.findall(r'[A-Za-z]+',brand.casefold())) | {'men','women','black','white','blue','green','gray','grey','new','model','original'}
    tokens=[t for t in tokens if t.casefold() not in blacklist and not any(t.casefold() in b.casefold().split() for b in BRANDS)]
    return ' '.join(dict.fromkeys(tokens[:3]))

def title_for(typ,brand,params,model,gender,lang,old):
    if not typ: return clean(old)[:180]
    label=TYPE_DATA[typ][0 if lang=='ua' else 1]
    g=gender_label(typ,gender,lang)
    color=color_value(param(params,'Колір'),lang)
    season=param(params,'Сезон')
    material=param(params,'Матеріал')
    # Never add unverified characteristics; no artificial title-length target.
    parts=[g,label,brand,model]
    for value in (color,season,material):
        if value and value.casefold() not in ' '.join(parts).casefold(): parts.append(value)
    result=clean(' '.join(p for p in parts if p))
    if len(result)<45 and old:
        # Supplier's actual title contains extra factual details; retain them instead of generic filler.
        extra=clean(old)
        for token in [brand,label,g]:
            if token: extra=re.sub(r'(?<!\w)'+re.escape(token)+r'(?!\w)',' ',extra,flags=re.I)
        extra=clean(extra)
        if extra and extra.casefold() not in result.casefold(): result=clean(result+' '+extra)
    return result[:180].rstrip(' ,-')

def keywords_for(typ,brand,params,model,gender,lang,title):
    if not typ: return clean(title)[:240]
    ix=0 if lang=='ua' else 1
    label=TYPE_DATA[typ][ix].lower()
    synonyms=TYPE_DATA[typ][2+ix]
    translit=BRANDS.get(brand,('',''))[ix] if brand else ''
    color=color_value(param(params,'Колір'),lang)
    season=param(params,'Сезон')
    size=param(params,'Розмір')
    g=gender_label(typ,gender,lang).lower()
    # Diverse, product-specific phrases; no generic price/order/Ukraine keyword padding.
    items=[]
    for term in [label]+synonyms:
        items.append(clean(f'{term} {brand}'))
    if translit: items.append(clean(f'{label} {translit}'))
    if g: items.append(clean(f'{g} {label} {brand}'))
    if model and len(model)<45: items.append(clean(f'{label} {brand} {model}'))
    if color: items.append(clean(f'{label} {brand} {color}'))
    if season: items.append(clean(f'{label} {brand} {season}'))
    if size and len(size)<=20 and not any(x in size for x in ',;/'):
        items.append(clean(f'{label} {brand} {size}'))
    seen=set(); out=[]; length=0
    for item in items:
        key=item.casefold()
        if len(item)<4 or key in seen: continue
        if length+len(item)+2>450: break
        out.append(item);seen.add(key);length+=len(item)+2
    return ', '.join(out)

def supplier_info(previous):
    # V4 has a dedicated supplier description block; preserve only this, not V4 boilerplate.
    m=re.search(r'<h3>\s*(?:Опис постачальника|Описание поставщика)\s*</h3>\s*<p>(.*?)</p>',previous or '',re.I|re.S)
    if not m: return ''
    return clean(re.sub(r'<[^>]*>',' ',html.unescape(m.group(1))))[:2500]

def description_for(title,params,code,lang,previous):
    ru=lang=='ru'; esc=lambda s: html.escape(str(s),quote=True)
    facts=[]; seen=set()
    for k,v in params:
        if k.casefold() in ('бренд у назві','стан') and v.casefold()=='потрібно уточнити нюанс у продавця': continue
        key=k.casefold()
        if key in seen: continue
        seen.add(key); facts.append(f'<li><strong>{esc(k)}:</strong> {esc(v)}</li>')
    supplier=supplier_info(previous)
    supplier_section=(f'<h3>{"Опис постачальника" if not ru else "Описание поставщика"}</h3><p>{esc(supplier)}</p>') if supplier else ''
    if ru:
        return (f'<h2>{esc(title)}</h2><p>Модель: {esc(title)}. Сведения о товаре, доступных вариантах и характеристиках приведены ниже.</p>'
                f'{supplier_section}<h3>Характеристики</h3><ul>{"".join(facts)}</ul>'
                '<p>Перед заказом проверьте выбранный размер, цвет и фотографии. Отсутствующие характеристики уточняйте у продавца.</p>'
                f'<p>Артикул: {esc(code)}. Наличие и цена обновляются по данным поставщика.</p>')
    return (f'<h2>{esc(title)}</h2><p>Модель: {esc(title)}. Відомості про товар, доступні варіанти та характеристики наведені нижче.</p>'
            f'{supplier_section}<h3>Характеристики</h3><ul>{"".join(facts)}</ul>'
            '<p>Перед замовленням перевірте обраний розмір, колір і фотографії. Відсутні характеристики уточнюйте у продавця.</p>'
            f'<p>Артикул: {esc(code)}. Наявність і ціна оновлюються за даними постачальника.</p>')

stats={'processed':0,'no_type':0,'with_brand':0}
for offer in tree.findall('.//offer'):
    params=get_params(offer)
    original=offer.findtext('name_ua') or offer.findtext('name') or ''
    typ=detect_type(original,params)
    brand=detect_brand(original,params)
    if brand: stats['with_brand']+=1
    if not typ: stats['no_type']+=1
    gender=detect_gender(original,params)
    model=source_model(offer,params,brand,typ)
    code=offer.findtext('vendorCode') or offer.get('id','')
    for lang in ('ua','ru'):
        suffix='_ua' if lang=='ua' else ''
        title=title_for(typ,brand,params,model,gender,lang,offer.findtext('name'+suffix) or original)
        get_node(offer,'name'+suffix).text=title
        get_node(offer,'keywords'+suffix).text=keywords_for(typ,brand,params,model,gender,lang,title)
        desc=get_node(offer,'description'+suffix)
        desc.text=description_for(title,params,code,lang,desc.text or '')
    stats['processed']+=1
path.parent.mkdir(parents=True,exist_ok=True)
tree.write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
print('SEO V6 complete:',stats,'Output:',path)
