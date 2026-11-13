"""MyDrop -> Prom YML. Python 3.11, requires lxml.
Preserves offer IDs, groups, pictures, supplier stock and variants.
Never invents materials, dimensions, originality or product features.
"""
from lxml import etree as ET
from collections import Counter
from pathlib import Path
import html, math, os, re, urllib.request

OUTPUT = Path('public/mydrop.xml')
SOURCE = os.environ.get('MYDROP_FEED_URL')
if not SOURCE:
    raise RuntimeError('Missing MYDROP_FEED_URL secret')
req = urllib.request.Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0 MyDropFeed/2.0'})
with urllib.request.urlopen(req, timeout=120) as response:
    data = response.read()
root = ET.fromstring(data)
offers = root.find('.//offers')
if offers is None:
    raise ValueError('No offers in supplier XML')
categories = {c.get('id'): (c.text or '').strip() for c in root.findall('.//categories/category')}

# Type, Ukrainian label, Russian label, commission %, target profit UAH.
TYPES = {
    'пуховик': ('пуховик', 'Пуховик', 'Пуховик', 19, 350),
    'куртка': ('куртка', 'Куртка', 'Куртка', 19, 250),
    'вітровка': ('вітровка', 'Вітровка', 'Ветровка', 19, 250),
    'олімпійка': ('олімпійка', 'Олімпійка', 'Олимпийка', 19, 250),
    'костюм': ('костюм', 'Костюм', 'Костюм', 19, 250),
    'шапка': ('шапка', 'Шапка', 'Шапка', 17, 200),
    'панама': ('панама', 'Панама', 'Панама', 18, 250),
    'футболка': ('футболка', 'Футболка', 'Футболка', 18, 300),
    'шорти': ('шорти', 'Шорти', 'Шорты', 18, 300),
    'майка': ('майка', 'Майка', 'Майка', 18, 300),
    'сукня': ('сукня', 'Сукня', 'Платье', 18, 300),
    'худі': ('худі', 'Худі', 'Худи', 18, 250),
    'зіпка': ('зіпка', 'Кофта на блискавці', 'Кофта на молнии', 18, 250),
    'кофта': ('кофта', 'Кофта', 'Кофта', 18, 250),
    'светр': ('светр', 'Светр', 'Свитер', 18, 250),
    'світшот': ('світшот', 'Світшот', 'Свитшот', 18, 250),
    'штани': ('штани', 'Штани', 'Штаны', 18, 250),
    'джинси': ('джинси', 'Джинси', 'Джинсы', 18, 250),
    'жилетка': ('жилетка', 'Жилетка', 'Жилетка', 18, 250),
    'сумка': ('сумка', 'Сумка', 'Сумка', 18, 250),
    'барсетка': ('барсетка', 'Барсетка', 'Барсетка', 18, 250),
    'рюкзак': ('рюкзак', 'Рюкзак', 'Рюкзак', 18, 250),
    'кепка': ('кепка', 'Кепка', 'Кепка', 18, 250),
    'гаманець': ('гаманець', 'Гаманець', 'Кошелек', 18, 250),
    'ремінь': ('ремінь', 'Ремінь', 'Ремень', 18, 250),
    'шкарпетки': ('шкарпетки', 'Шкарпетки', 'Носки', 18, 250),
    'аксесуар': ('аксесуар', 'Аксесуар', 'Аксессуар', 18, 250),
}
ALIASES = [
    ('пуховик', 'пуховик'), ('куртк', 'куртка'), ('вітровк', 'вітровка'),
    ('ветровк', 'вітровка'), ('олімпійк', 'олімпійка'), ('олимпийк', 'олімпійка'),
    ('костюм', 'костюм'), ('шапк', 'шапка'), ('панам', 'панама'),
    ('футболк', 'футболка'), ('шорт', 'шорти'), ('майк', 'майка'),
    ('сукн', 'сукня'), ('плать', 'сукня'), ('худі', 'худі'), ('худи', 'худі'),
    ('зіпк', 'зіпка'), ('зипк', 'зіпка'), ('светр', 'светр'), ('свитер', 'светр'),
    ('світшот', 'світшот'), ('свитшот', 'світшот'), ('штани', 'штани'),
    ('штаны', 'штани'), ('джинс', 'джинси'), ('жилет', 'жилетка'),
    ('кофт', 'кофта'), ('барсет', 'барсетка'), ('сумк', 'сумка'),
    ('рюкзак', 'рюкзак'), ('кепк', 'кепка'), ('гаман', 'гаманець'),
    ('кошел', 'гаманець'), ('ремін', 'ремінь'), ('ремень', 'ремінь'),
    ('шкарпет', 'шкарпетки'), ('носк', 'шкарпетки'),
]
CATEGORY_FALLBACK = {
    '170231': 'пуховик', '170198': 'куртка', '170196': 'костюм',
    '170183': 'шапка', '170191': 'футболка', '170192': 'шорти',
    '170195': 'кофта', '170193': 'штани', '170194': 'джинси',
    '170182': 'кепка', '170184': 'ремінь', '170188': 'гаманець',
    '170311': 'рюкзак', '170755': 'рюкзак', '170756': 'сумка',
}
COLORS = [
    (r'\bчорн(?:ий|а|е|і)\b', 'чорний', 'черный'),
    (r'\bчёрн(?:ый|ая|ое)\b', 'чорний', 'черный'),
    (r'\bбіл(?:ий|а|е|і)\b', 'білий', 'белый'),
    (r'\bwhite\b', 'білий', 'белый'),
    (r'\bblack\b', 'чорний', 'черный'),
    (r'\bсір(?:ий|а|е|і)\b', 'сірий', 'серый'),
    (r'\bgray\b|\bgrey\b', 'сірий', 'серый'),
    (r'\bсин(?:ій|я|є|і)\b', 'синій', 'синий'),
    (r'\bblue\b', 'синій', 'синий'),
    (r'\bзелен(?:ий|а|е|і)\b', 'зелений', 'зеленый'),
    (r'\bgreen\b', 'зелений', 'зеленый'),
    (r'\bкоричнев(?:ий|а|е|і)\b', 'коричневий', 'коричневый'),
    (r'\bbrown\b', 'коричневий', 'коричневый'),
    (r'\bрожев(?:ий|а|е|і)\b', 'рожевий', 'розовый'),
    (r'\bpink\b', 'рожевий', 'розовый'),
]
BRANDS = ['Nike', 'Jordan', 'Adidas', 'New Balance', 'Puma', 'Lacoste', 'Burberry',
          'Moncler', 'Armani Exchange', 'Calvin Klein', 'Patagonia', 'HELLSTAR',
          'Chrome Hearts', 'Stone Island', 'Supreme', 'Carhartt', 'Maison Margiela',
          'Palm Angels', 'The North Face', 'Off-White', 'Balenciaga', 'Gucci',
          'Louis Vuitton', 'Dior', 'Prada', 'Ralph Lauren', 'Tommy Hilfiger',
          'Under Armour', 'Essentials', 'Fear of God', 'Loro Piana']

def set_text(offer, key, value):
    node = offer.find(key)
    if node is None:
        node = ET.SubElement(offer, key)
    node.text = str(value)

def clean(value):
    return re.sub(r'\s+', ' ', value or '').strip(' \t\r\n-–|,')

def detect_type(name, category_id):
    low = name.casefold()
    for fragment, typ in ALIASES:
        if fragment in low:
            return typ
    return CATEGORY_FALLBACK.get(category_id, 'аксесуар')

def detect_brand(name):
    for brand in sorted(BRANDS, key=len, reverse=True):
        if re.search(r'(?<!\w)' + re.escape(brand) + r'(?!\w)', name, re.I):
            return brand
    return ''

def detect_color(name):
    for pattern, ua, ru in COLORS:
        if re.search(pattern, name, re.I):
            return ua, ru
    return '', ''

def unique_join(items, max_len=1024):
    output, seen, total = [], set(), 0
    for item in items:
        item = clean(item)
        key = item.casefold()
        if len(item) < 3 or key in seen:
            continue
        extra = len(item) + (2 if output else 0)
        if total + extra > max_len:
            continue
        output.append(item)
        seen.add(key)
        total += extra
    return ', '.join(output)

def size_of(offer):
    for p in offer.findall('param'):
        if (p.get('name') or '').casefold() in ('размер', 'розмір', 'size'):
            return clean(p.text)
    return ''

def put_param(offer, key, value):
    if value and not any(p.get('name', '').casefold() == key.casefold() for p in offer.findall('param')):
        ET.SubElement(offer, 'param', name=key).text = value

def description(label, brand, model, color, size, code, category, ru=False):
    esc = html.escape
    title = clean(f'{label} {model}')
    rows = []
    if brand:
        rows.append(('Бренд у назві' if not ru else 'Бренд в названии', brand))
    if color:
        rows.append(('Колір' if not ru else 'Цвет', color))
    if size:
        rows.append(('Розмір / варіант' if not ru else 'Размер / вариант', size))
    rows.extend([('Категорія' if not ru else 'Категория', category),
                 ('Артикул' if not ru else 'Артикул', code)])
    rows_html = ''.join(f'<li><strong>{esc(k)}:</strong> {esc(v)}</li>' for k, v in rows if v)
    if ru:
        intro = (f'{esc(title)} — модель из категории «{esc(category)}». '
                 'В карточке сохранены фотографии поставщика и доступные варианты. '
                 'Выбирайте подходящий вариант по указанным характеристикам.')
        tip = ('Перед заказом проверьте размер и фотографии. Если важны состав ткани, '
               'точные замеры, комплектация или другие детали, уточните их у продавца: '
               'эти сведения не подтверждены исходной выгрузкой.')
        footer = ('Чтобы быстро уточнить наличие и вариант, укажите артикул '
                  f'{esc(code)}. Оформление заказа — через Prom.ua.')
        return (f'<h2>{esc(title)}</h2><p>{intro}</p>'
                f'<h3>Характеристики товара</h3><ul>{rows_html}</ul>'
                f'<h3>Как выбрать</h3><p>{tip}</p><h3>Заказ</h3><p>{footer}</p>')
    intro = (f'{esc(title)} — модель із категорії «{esc(category)}». '
             'У картці збережено фотографії постачальника та доступні варіанти. '
             'Оберіть відповідний варіант за вказаними характеристиками.')
    tip = ('Перед замовленням перевірте розмір і фотографії. Якщо важливі склад тканини, '
           'точні заміри, комплектація чи інші деталі, уточніть їх у продавця: '
           'ці дані не підтверджені вихідною вигрузкою.')
    footer = (f'Для швидкого уточнення наявності та варіанта назвіть артикул {esc(code)}. '
              'Замовлення оформлюється через Prom.ua.')
    return (f'<h2>{esc(title)}</h2><p>{intro}</p>'
            f'<h3>Характеристики товару</h3><ul>{rows_html}</ul>'
            f'<h3>Як обрати</h3><p>{tip}</p><h3>Замовлення</h3><p>{footer}</p>')

stats = Counter()
for offer in list(offers):
    original = clean(offer.findtext('name'))
    category_id = offer.findtext('categoryId') or ''
    typ = detect_type(original, category_id)
    _, ua_label, ru_label, fee, profit = TYPES[typ]
    try:
        base = float(clean(offer.findtext('price')).replace(',', '.'))
        if not math.isfinite(base) or base <= 0:
            raise ValueError('invalid price')
    except (ValueError, TypeError):
        offers.remove(offer)
        stats['excluded_without_price'] += 1
        continue
    # Do not misclassify sleeveless puffer as a regular jacket.
    if typ == 'пуховик' and 'жилет' in original.casefold():
        ua_label, ru_label = 'Пуховик-жилетка', 'Пуховик-жилетка'
    code = clean(offer.findtext('vendorCode')) or offer.get('id', '')
    size = size_of(offer)
    brand = detect_brand(original)
    color_ua, color_ru = detect_color(original)
    # Remove only a leading product type, leaving model/brand and original qualifiers.
    model = re.sub(r'^(?:пуховик(?:\s*[-–]?\s*жилетка)?|куртка|вітровка|ветровка|олімпійка|олимпийка|костюм|шапка|панама|футболка|шорти|майка|сукня|платье|худі|худи|зіпка|зипка|кофта|светр|свитер|світшот|свитшот|штани|штаны|джинси|жилетка|сумка|барсетка|рюкзак|кепка|гаманець|кошелек|ремінь|ремень|шкарпетки|носки)\b\s*[-–]?\s*', '', original, flags=re.I)
    model = clean(model) or original
    # Preserve supplied model identity; size stays a separate variation parameter.
    title_ua = clean(f'{ua_label} {model}')[:240]
    title_ru = clean(f'{ru_label} {model}')[:240]
    set_text(offer, 'name_ua', title_ua)
    set_text(offer, 'name', title_ru)
    set_text(offer, 'price', math.ceil((base + profit) / (1 - fee / 100)))
    category = categories.get(category_id, typ)
    put_param(offer, 'Тип товару', ua_label)
    put_param(offer, 'Артикул', code)
    if brand:
        put_param(offer, 'Бренд у назві', brand)
    if color_ua:
        put_param(offer, 'Колір', color_ua)
    if size:
        put_param(offer, 'Розмір', size)
    if 'нюанс' in size.casefold() or 'нюанс' in original.casefold():
        put_param(offer, 'Стан', 'Потрібно уточнити нюанс у продавця')
    # Query variants based on real words from supplier; not asserted search volume.
    term_ua = clean(f'{ua_label.lower()} {model}')
    term_ru = clean(f'{ru_label.lower()} {model}')
    brand_term_ua = clean(f'{ua_label.lower()} {brand}') if brand else ''
    brand_term_ru = clean(f'{ru_label.lower()} {brand}') if brand else ''
    ua_terms = [term_ua, brand_term_ua, f'купити {term_ua}', f'{term_ua} ціна',
                f'{term_ua} замовити', f'{term_ua} Україна', f'{model} {ua_label.lower()}']
    ru_terms = [term_ru, brand_term_ru, f'купить {term_ru}', f'{term_ru} цена',
                f'{term_ru} заказать', f'{term_ru} Украина', f'{model} {ru_label.lower()}']
    if brand:
        ua_terms += [f'{brand} {ua_label.lower()}', f'купити {ua_label.lower()} {brand}']
        ru_terms += [f'{brand} {ru_label.lower()}', f'купить {ru_label.lower()} {brand}']
    if color_ua:
        ua_terms += [f'{brand_term_ua or ua_label.lower()} {color_ua}', f'{term_ua} {color_ua}']
        ru_terms += [f'{brand_term_ru or ru_label.lower()} {color_ru}', f'{term_ru} {color_ru}']
    if size and len(size) < 20:
        ua_terms.append(f'{term_ua} {size}')
        ru_terms.append(f'{term_ru} {size}')
    set_text(offer, 'keywords_ua', unique_join(ua_terms))
    set_text(offer, 'keywords', unique_join(ru_terms))
    set_text(offer, 'description_ua', description(ua_label, brand, model, color_ua, size, code, category))
    set_text(offer, 'description', description(ru_label, brand, model, color_ru, size, code, category, ru=True))
    stats[typ] += 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
ET.ElementTree(root).write(str(OUTPUT), encoding='utf-8', xml_declaration=True, pretty_print=True)
print('Offers:', len(offers), 'Excluded:', stats['excluded_without_price'], 'Breakdown:', dict(stats))
print('Output:', OUTPUT)
