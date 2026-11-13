"""MyDrop -> Prom SEO V9. Run V4 pricing/stock builder first; improve SEO only.
Requires build_mydrop_github_SEO_v4.py in repo root and lxml.
"""
import runpy
import re
import html
from pathlib import Path
from lxml import etree as ET

if __import__('os').environ.get('SEO_TEST_EXISTING_XML') != '1':
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

# Neutral category-search phrases: these describe the category/use, not unverified
# material, authenticity, gender, design, season, or manufacturing claims.
TITLE_EXTENSIONS = {
    'худі': ('кофта худі, толстовка для повсякденних образів', 'худи, толстовка для повседневных образов'),
    'пуховик': ('верхній одяг, куртка для повсякденного гардероба', 'верхняя одежда, куртка для повседневного гардероба'),
    'куртка': ('верхній одяг для повсякденного гардероба', 'верхняя одежда для повседневного гардероба'),
    'вітровка': ('легка куртка, верхній одяг для повсякденних образів', 'легкая куртка, верхняя одежда для повседневных образов'),
    'олімпійка': ('спортивна кофта для повсякденних образів', 'спортивная кофта для повседневных образов'),
    'костюм': ('комплект одягу для повсякденних образів', 'комплект одежды для повседневных образов'),
    'футболка': ('футболка для повсякденних образів та гардероба', 'футболка для повседневных образов и гардероба'),
    'штани': ('штани для повсякденного гардероба та образів', 'штаны для повседневного гардероба и образов'),
    'шорти': ('шорти для повсякденного гардероба та образів', 'шорты для повседневного гардероба и образов'),
    'сумка': ('сумка, аксесуар для повсякденних образів', 'сумка, аксессуар для повседневных образов'),
    'рюкзак': ('рюкзак, аксесуар для повсякденного використання', 'рюкзак, аксессуар для повседневного использования'),
    'кепка': ('кепка, бейсболка для повсякденних образів', 'кепка, бейсболка для повседневных образов'),
    'шапка': ('головний убір для повсякденного гардероба', 'головной убор для повседневного гардероба'),
}
GENERAL_EXTENSIONS = (
    'для повсякденного гардероба та образів',
    'для повседневного гардероба и образов',
)

def title_for(typ,brand,params,model,gender,lang,old):
    """Prefer factual attributes; pad with neutral category language only if useful."""
    if not typ:
        return clean(old)[:100]
    ix=0 if lang=='ua' else 1
    label=TYPE_DATA[typ][ix]
    g=gender_label(typ,gender,lang)
    alias=BRANDS.get(brand,('',''))[ix] if brand else ''
    parts=[g,label,brand]
    if alias and alias.casefold()!=brand.casefold(): parts.append('('+alias+')')
    if model and model.casefold() not in ' '.join(parts).casefold(): parts.append(model)
    color=color_value(param(params,'Колір'),lang)
    season=param(params,'Сезон')
    material=param(params,'Матеріал')
    size=param(params,'Розмір')
    for val in (color,season,material):
        if val and len(val)<45 and val.casefold() not in ' '.join(parts).casefold() and len(clean(' '.join(parts+[val])))<=100:
            parts.append(val)
    if size and len(size)<=15 and not any(x in size for x in ',;/'):
        sizeword='розмір' if lang=='ua' else 'размер'
        if len(clean(' '.join(parts+[sizeword,size])))<=100: parts.extend([sizeword,size])
    base=clean(' '.join(x for x in parts if x))
    if len(base)>=70: return base[:100].rstrip(' ,;-')
    extra=TITLE_EXTENSIONS.get(typ,GENERAL_EXTENSIONS)[ix]
    # Use one readable search-oriented phrase; never truncate mid-word.
    candidates=[base+' — '+extra, base+', '+extra, base]
    for candidate in candidates:
        if 70<=len(candidate)<=100:
            return candidate
    if len(base)<70:
        candidate=base+' — '+extra
        if len(candidate)>100:
            candidate=candidate[:101].rsplit(' ',1)[0].rstrip(' ,;–-')
        return candidate
    return base[:100].rstrip(' ,;-')

def keywords_for(typ,brand,params,model,gender,lang,title):
    if not typ: return clean(title)[:240]
    ix=0 if lang=='ua' else 1
    label=TYPE_DATA[typ][ix].lower()
    aliases=TYPE_DATA[typ][2+ix]
    cyr=BRANDS.get(brand,('',''))[ix] if brand else ''
    color=color_value(param(params,'Колір'),lang)
    size=param(params,'Розмір')
    genderword=gender_label(typ,gender,lang).lower()
    terms=[]
    for word in dict.fromkeys([label]+aliases):
        terms.append(clean(f'{word} {brand}'))
    if cyr and cyr.casefold()!=brand.casefold():
        for word in dict.fromkeys([label]+aliases[:2]): terms.append(clean(f'{word} {cyr}'))
    if genderword: terms.append(clean(f'{genderword} {label} {brand}'))
    if model and len(model)<=35: terms.append(clean(f'{label} {brand} {model}'))
    if color: terms.append(clean(f'{label} {brand} {color}'))
    if size and len(size)<12 and not any(c in size for c in ',;/'): terms.append(clean(f'{label} {brand} {size}'))
    # English hoodie is a genuine alternate search spelling, not an invented product property.
    if typ=='худі' and brand: terms.append(f'{brand} hoodie')
    unique=[];seen=set()
    for term in terms:
        key=term.casefold()
        if key and key not in seen and len(', '.join(unique+[term]))<=500:
            seen.add(key);unique.append(term)
    return ', '.join(unique)

def supplier_info(previous):
    # V4 has a dedicated supplier description block; preserve only this, not V4 boilerplate.
    m=re.search(r'<h3>\s*(?:Опис постачальника|Описание поставщика)\s*</h3>\s*<p>(.*?)</p>',previous or '',re.I|re.S)
    if not m: return ''
    return clean(re.sub(r'<[^>]*>',' ',html.unescape(m.group(1))))[:2500]

def description_for(title,params,code,lang,previous):
    ru=lang=='ru'; esc=lambda s: html.escape(str(s),quote=True)
    label='Характеристики' if not ru else 'Характеристики'
    rows=[];seen=set()
    for k,v in params:
        if k.casefold() in ('стан',) and 'уточн' in v.casefold(): continue
        if k.casefold() in seen: continue
        seen.add(k.casefold())
        rows.append(f'<li><strong>{esc(k)}:</strong> {esc(v)}</li>')
    supplier=supplier_info(previous)
    lead=('Доступні характеристики цього товару наведено нижче.' if not ru else 'Доступные характеристики товара указаны ниже.')
    source=(f'<h3>{"Дані постачальника" if not ru else "Данные поставщика"}</h3><p>{esc(supplier)}</p>') if supplier else ''
    size=param(params,'Розмір'); color=param(params,'Колір')
    specific=[]
    if size: specific.append(('Розмір' if not ru else 'Размер')+': '+size)
    if color: specific.append(('Колір' if not ru else 'Цвет')+': '+color)
    factsline=esc('; '.join(specific))
    intro=f'<p>{factsline}.</p>' if specific else f'<p>{lead}</p>'
    order=('Для замовлення звірте обраний варіант із фотографіями та характеристиками.' if not ru else 'Перед заказом сверьте выбранный вариант с фотографиями и характеристиками.')
    return f'<h2>{esc(title)}</h2>{intro}{source}<h3>{label}</h3><ul>{"".join(rows)}</ul><p>{order}</p><p>{"Артикул" if not ru else "Артикул"}: {esc(code)}</p>'

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
print('SEO V9 complete:',stats,'Output:',path)
