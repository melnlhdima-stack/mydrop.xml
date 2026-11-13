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
          'Louis Vuitton', 'Dior', 'Prada', 'Polo Ralph Lauren', 'Ralph Lauren', 'Tommy Hilfiger',
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


# SEO v3: category-aware vocabulary. Only facts present in supplier data are asserted.
BRAND_CYR = {
 'Patagonia': ('Патагонія','Патагония'), 'Ralph Lauren': ('Ральф Лорен','Ральф Лорен'),
 'Polo Ralph Lauren': ('Поло Ральф Лорен','Поло Ральф Лорен'),
 'Nike': ('Найк','Найк'), 'Adidas': ('Адідас','Адидас'),
 'Jordan': ('Джордан','Джордан'), 'Burberry': ('Берберрі','Берберри'),
 'Moncler': ('Монклер','Монклер'), 'HELLSTAR': ('Хеллстар','Хеллстар'),
 'New Balance': ('Нью Беланс','Нью Баланс'), 'Stone Island': ('Стоун Айленд','Стоун Айленд'),
 'Supreme': ('Супрім','Суприм'), 'The North Face': ('Норт Фейс','Норт Фейс'),
 'Lacoste': ('Лакост','Лакост'), 'Carhartt': ('Кархарт','Кархарт'),
 'Chrome Hearts': ('Хром Хартс','Хром Хартс'), 'Maison Margiela': ('Мезон Маржела','Мезон Маржела'),
 'Palm Angels': ('Палм Енджелс','Палм Энджелс'), 'Tommy Hilfiger': ('Томмі Хілфігер','Томми Хилфигер')
}
TYPE_SYNONYMS = {
 'пуховик': (['пуховик','куртка пуховик','зимовий пуховик'], ['пуховик','куртка пуховик','зимний пуховик']),
 'куртка': (['куртка','верхній одяг'], ['куртка','верхняя одежда']),
 'худі': (['худі','кофта худі','худи'], ['худи','толстовка','кофта худи']),
 'сумка': (['сумка','сумочка'], ['сумка','сумочка']),
 'барсетка': (['барсетка','сумка','сумка через плече'], ['барсетка','сумка','сумка через плечо']),
 'рюкзак': (['рюкзак','наплічник'], ['рюкзак','ранец']),
 'шорти': (['шорти','чоловічі шорти'], ['шорты','мужские шорты']),
 'штани': (['штани','брюки'], ['штаны','брюки']),
 'футболка': (['футболка','футболка з принтом'], ['футболка','футболка с принтом']),
 'костюм': (['костюм','комплект одягу'], ['костюм','комплект одежды']),
 'кепка': (['кепка','бейсболка'], ['кепка','бейсболка']),
 'шапка': (['шапка','головний убір'], ['шапка','головной убор']),
 'жилетка': (['жилетка','жилет'], ['жилетка','жилет']),
}

def source_facts(offer):
    result=[]
    for param in offer.findall('param'):
        key=clean(param.get('name'))
        value=clean(param.text)
        if key and value and len(value)<250 and len(key)<90:
            result.append((key,value))
    return result

def gender_of(original, category):
    text=(original+' '+category).casefold()
    if re.search(r'\b(чоловіч|мужск|men\b|mens\b)',text): return ('Чоловічий','Мужской','чоловіча','мужская')
    if re.search(r'\b(жіноч|женск|women\b|womens\b)',text): return ('Жіночий','Женский','жіноча','женская')
    return ('','','','')

def season_of(original, facts):
    text=(original+' '+' '.join(v for k,v in facts if any(t in k.casefold() for t in ['сезон','season','опис','назва']))).casefold()
    if 'зимов' in text or 'зимн' in text: return ('зимовий','зимний')
    if 'демісезон' in text or 'демисезон' in text: return ('демісезонний','демисезонный')
    if 'літн' in text or 'летн' in text: return ('літній','летний')
    return ('','')

def build_title(label, brand, model, color, season, gender, code, lang='ua'):
    # Keep supplier-specific model and confirmed details without repeating brand/type.
    rest = clean(model)
    if brand:
        rest = re.sub(r'(?<!\w)' + re.escape(brand) + r'(?!\w)', ' ', rest, flags=re.I)
    rest = re.sub(r'\b(?:чоловічий|чоловіча|чоловічі|жіночий|жіноча|жіночі|мужской|мужская|женский|женская)\b', ' ', rest, flags=re.I)
    for piece in (color, season):
        if piece:
            rest = re.sub(r'(?<!\w)' + re.escape(piece) + r'(?!\w)', ' ', rest, flags=re.I)
    rest = clean(rest)
    feminine = label.casefold() in ('сумка','барсетка','шапка','куртка','футболка','панама','жилетка','кофта','сукня','кепка','вітровка','ветровка','олімпійка','олимпийка','майка')
    if gender:
        female = gender.casefold().startswith(('жіноч', 'женск'))
        if lang == 'ua':
            gender = ('Жіноча' if female else 'Чоловіча') if feminine else ('Жіночий' if female else 'Чоловічий')
        else:
            gender = ('Женская' if female else 'Мужская') if feminine else ('Женский' if female else 'Мужской')
    title = clean(' '.join(x for x in (gender, label, brand, rest, color, season) if x))
    return title[:230].rstrip(' ,-')


def build_keywords(typ, brand, model, color, size, season, gender, lang):
    ix = 0 if lang == 'ua' else 1
    synonyms = TYPE_SYNONYMS.get(typ, ([TYPES[typ][1].lower()], [TYPES[typ][2].lower()]))[ix]
    label = TYPES[typ][1 + ix].lower()
    brand_cyr = BRAND_CYR.get(brand, ('', ''))[ix] if brand else ''
    brands = [b for b in (brand, brand_cyr) if b]
    buy = 'купити' if lang == 'ua' else 'купить'
    price = 'ціна' if lang == 'ua' else 'цена'
    order = 'замовити' if lang == 'ua' else 'заказать'
    country = 'Україна' if lang == 'ua' else 'Украина'
    feminine = typ in ('сумка','барсетка','куртка','футболка','кепка','шапка','майка','панама','вітровка','олімпійка','жилетка','кофта','сукня')
    if gender:
        female = gender.casefold().startswith(('жіноч', 'женск'))
        if lang == 'ua':
            prefix = ('жіноча' if female else 'чоловіча') if feminine else ('жіночий' if female else 'чоловічий')
        else:
            prefix = ('женская' if female else 'мужская') if feminine else ('женский' if female else 'мужской')
    else:
        prefix = ''
    items = []
    for word in dict.fromkeys([label] + synonyms):
        for b in brands:
            core = f'{word} {b}'
            items.extend((core, f'{b} {word}', f'{buy} {core}', f'{core} {price}', f'{order} {core}', f'{core} {country}'))
            if prefix:
                items.extend((f'{prefix} {core}', f'{word} {b} {prefix}'))
            if color:
                items.append(f'{core} {color}')
            if season:
                items.append(f'{core} {season}')
            if size and len(size) <= 12:
                items.append(f'{core} {size}')
    if not brands:
        base = clean(f'{label} {model}')
        items.extend((base, f'{buy} {base}', f'{base} {price}'))
    # More terms only when genuinely different, never filler or made-up properties.
    return unique_join(items, max_len=1024)


def detailed_description(title, typ, brand, color, season, size, code, category, facts, lang, supplier_description=""):
    ru=lang=='ru'; esc=html.escape
    def e(x): return esc(str(x),quote=True)
    pairs=[]; seen=set()
    for k,v in facts:
        if k.casefold() not in seen:
            pairs.append((k,v));seen.add(k.casefold())
    pairs.extend([('Бренд у назві' if not ru else 'Бренд в названии',brand),
                  ('Колір' if not ru else 'Цвет',color),
                  ('Сезон' if not ru else 'Сезон',season),
                  ('Розмір / варіант' if not ru else 'Размер / вариант',size),
                  ('Категорія' if not ru else 'Категория',category),
                  ('Артикул' if not ru else 'Артикул',code)])
    facts_html=''.join(f'<li><strong>{e(k)}:</strong> {e(v)}</li>' for k,v in pairs if v)
    supplier_text = clean(re.sub(r'<[^>]+>', ' ', html.unescape(supplier_description or '')))
    supplier_html = f'<h3>{"Опис постачальника" if not ru else "Описание поставщика"}</h3><p>{e(supplier_text[:4500])}</p>' if supplier_text else ''
    if ru:
        return (f'<h2>{e(title)}</h2>'
          f'<p>{e(title)} — товар из раздела «{e(category)}». В карточке указаны доступные сведения о модели и фотографии поставщика. '
          'Сравните размер, вариант и характеристики, чтобы выбрать подходящую позицию.</p>'
          '<h3>Описание модели</h3><p>Для выбора ориентируйтесь на название модели, фотографии и параметры ниже. '
          'Если нужного свойства нет в перечне, оно не подтверждено поставщиком и требует уточнения.</p>'
          f'{supplier_html}<h3>Характеристики и параметры</h3><ul>{facts_html}</ul>'
          '<h3>Размер, цвет и детали</h3><p>Перед оформлением заказа проверьте доступный размер и цвет, '
          'а также изображения выбранного варианта. Материал, состав, размеры изделия и комплектация указываются '
          'только при наличии этих данных в исходной карточке.</p>'
          f'<h3>Как заказать</h3><p>Для уточнения модели назовите артикул {e(code)}. '
          'Оформляйте заказ через магазин на Prom.ua. Наличие и стоимость обновляются по данным поставщика.</p>')
    return (f'<h2>{e(title)}</h2>'
      f'<p>{e(title)} — товар із розділу «{e(category)}». У картці наведено доступні відомості про модель і фотографії постачальника. '
      'Порівняйте розмір, варіант і характеристики, щоб обрати відповідну позицію.</p>'
      '<h3>Опис моделі</h3><p>Під час вибору орієнтуйтеся на назву моделі, фотографії та параметри нижче. '
      'Якщо потрібної властивості немає у переліку, вона не підтверджена постачальником і потребує уточнення.</p>'
      f'{supplier_html}<h3>Характеристики та параметри</h3><ul>{facts_html}</ul>'
      '<h3>Розмір, колір та деталі</h3><p>Перед оформленням замовлення перевірте доступний розмір і колір, '
      'а також зображення обраного варіанта. Матеріал, склад, заміри виробу та комплектація зазначаються '
      'лише за наявності цих даних у вихідній картці.</p>'
      f'<h3>Як замовити</h3><p>Для уточнення моделі назвіть артикул {e(code)}. '
      'Оформлюйте замовлення через магазин на Prom.ua. Наявність і вартість оновлюються за даними постачальника.</p>')

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
    if size.casefold() in ('oni size', 'one size', 'onesize', 'універсальний', 'универсальный'):
        size = 'універсальний' if size.casefold() not in ('oni size',) else ''
    brand = detect_brand(original)
    color_ua, color_ru = detect_color(original)
    # Remove only a leading product type, leaving model/brand and original qualifiers.
    model = re.sub(r'^(?:пуховик(?:\s*[-–]?\s*жилетка)?|куртка|вітровка|ветровка|олімпійка|олимпийка|костюм|шапка|панама|футболка|шорти|майка|сукня|платье|худі|худи|зіпка|зипка|кофта|светр|свитер|світшот|свитшот|штани|штаны|джинси|жилетка|сумка|барсетка|рюкзак|кепка|гаманець|кошелек|ремінь|ремень|шкарпетки|носки)\b\s*[-–]?\s*', '', original, flags=re.I)
    model = clean(model) or original
    category = categories.get(category_id, typ)
    facts = source_facts(offer)
    supplier_description_ru = offer.findtext('description') or ''
    supplier_description_ua = offer.findtext('description_ua') or supplier_description_ru
    gender_ua, gender_ru, _, _ = gender_of(original, category)
    season_ua, season_ru = season_of(original, facts)
    title_ua = build_title(ua_label, brand, model, color_ua, season_ua, gender_ua, code)
    title_ru = build_title(ru_label, brand, model, color_ru, season_ru, gender_ru, code, 'ru')
    set_text(offer, 'name_ua', title_ua)
    set_text(offer, 'name', title_ru)
    set_text(offer, 'price', math.ceil((base + profit) / (1 - fee / 100)))
    put_param(offer, 'Тип товару', ua_label)
    put_param(offer, 'Артикул', code)
    if brand: put_param(offer, 'Бренд у назві', brand)
    if color_ua: put_param(offer, 'Колір', color_ua)
    if size: put_param(offer, 'Розмір', size)
    if season_ua: put_param(offer, 'Сезон', season_ua)
    if gender_ua: put_param(offer, 'Стать', 'Чоловіча' if gender_ua.startswith('Ч') else 'Жіноча')
    if 'нюанс' in size.casefold() or 'нюанс' in original.casefold():
        put_param(offer, 'Стан', 'Потрібно уточнити нюанс у продавця')
    set_text(offer, 'keywords_ua', build_keywords(typ, brand, model, color_ua, size, season_ua, gender_ua, 'ua'))
    set_text(offer, 'keywords', build_keywords(typ, brand, model, color_ru, size, season_ru, gender_ru, 'ru'))
    set_text(offer, 'description_ua', detailed_description(title_ua, typ, brand, color_ua, season_ua, size, code, category, facts, 'ua', supplier_description_ua))
    set_text(offer, 'description', detailed_description(title_ru, typ, brand, color_ru, season_ru, size, code, category, facts, 'ru', supplier_description_ru))
    stats[typ] += 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
ET.ElementTree(root).write(str(OUTPUT), encoding='utf-8', xml_declaration=True, pretty_print=True)
print('Offers:', len(offers), 'Excluded:', stats['excluded_without_price'], 'Breakdown:', dict(stats))
print('Output:', OUTPUT)
