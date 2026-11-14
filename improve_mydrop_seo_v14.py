#!/usr/bin/env python3
"""MyDrop SEO V13: safe bilingual postprocessor for Prom.ua YML/XML.

Usage: python improve_mydrop_seo_v12.py public/mydrop.xml
Only writes name, name_ua, keywords, keywords_ua, description, description_ua.
Keeps all offer IDs, prices, images, availability, categories and params intact.
"""
import argparse
import html
import re
from collections import Counter
import csv
from pathlib import Path
from lxml import etree

# Ukrainian name, Russian name, Ukrainian synonym, Russian synonym.
TYPES = {
    "Худі": ("худі", "худи", "кофта з капюшоном", "кофта с капюшоном"),
    "Штани": ("штани", "штаны", "спортивні штани", "спортивные штаны"),
    "Джинси": ("джинси", "джинсы", "джинсові штани", "джинсовые брюки"),
    "Куртка": ("куртка", "куртка", "", ""),
    "Футболка": ("футболка", "футболка", "", ""),
    "Костюм": ("костюм", "костюм", "комплект одягу", "комплект одежды"),
    "Жилетка": ("жилетка", "жилетка", "жилет", "жилет"),
    "Шорти": ("шорти", "шорты", "", ""),
    "Рюкзак": ("рюкзак", "рюкзак", "", ""),
    "Сумка": ("сумка", "сумка", "", ""),
    "Кепка": ("кепка", "кепка", "бейсболка", "бейсболка"),
    "Шапка": ("шапка", "шапка", "", ""),
    "Шкарпетки": ("шкарпетки", "носки", "", ""),
    "Олімпійка": ("олімпійка", "олимпийка", "кофта на блискавці", "кофта на молнии"),
    "Кофта на блискавці": ("кофта на блискавці", "кофта на молнии", "", ""),
    "Кофта": ("кофта", "кофта", "", ""),
    "Світшот": ("світшот", "свитшот", "", ""),
    "Пуховик": ("пуховик", "пуховик", "", ""),
    "Кросівки": ("кросівки", "кроссовки", "", ""),
    "Шльопанці": ("шльопанці", "шлепанцы", "", ""),
    "Сорочка": ("сорочка", "рубашка", "", ""),
    "Поло": ("поло", "поло", "", ""),
    "Спідниця": ("спідниця", "юбка", "", ""),
    "Сукня": ("сукня", "платье", "", ""),
    "Лонгслів": ("лонгслів", "лонгслив", "", ""),
    "Кардиган": ("кардиган", "кардиган", "", ""),
    "Аксесуар": ("аксесуар", "аксессуар", "", ""),
    "Ремінь": ("ремінь", "ремень", "", ""),
    "Гаманець": ("гаманець", "кошелек", "", ""),
    "Барсетка": ("барсетка", "барсетка", "", ""),
    "Светр": ("светр", "свитер", "", ""),
}
COLORS = {
    "чорний": "черный", "білий": "белый", "сірий": "серый",
    "синій": "синий", "зелений": "зеленый", "червоний": "красный",
    "коричневий": "коричневый", "бежевий": "бежевый",
    "рожевий": "розовый", "жовтий": "желтый",
    "блакитний": "голубой", "фіолетовий": "фиолетовый",
    "помаранчевий": "оранжевый",
}
RU_TO_UA = {v: k for k, v in COLORS.items()}
SIZE_KEYS = ("розмір", "размер")
COLOR_KEYS = ("колір", "цвет")
BRAND_KEYS = ("бренд у назві", "бренд в названии")
MODEL_KEYS = ("модель",)
UNSAFE_UA = re.compile(r"\b(худи|толстовка|штаны|шорты|джинсы|размер|черный|белый|серый|красный|синий|свитер|кошелек)\b", re.I)
UNSAFE_RU = re.compile(r"\b(худі|штани|шорти|джинси|розмір|чорний|білий|сірий|червоний|светр|гаманець)\b", re.I)

def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()

def field(offer, key):
    return clean(offer.findtext(key))

def set_field(offer, key, value):
    node = offer.find(key)
    if node is None:
        node = etree.SubElement(offer, key)
    node.text = value

def get_params(offer):
    params = {}
    for node in offer.findall("param"):
        key = clean(node.get("name")).casefold()
        if key and clean(node.text):
            params.setdefault(key, clean(node.text))
    return params

def first(params, keys):
    return next((params[k] for k in keys if params.get(k)), "")

def detect_type(offer, params):
    declared = first(params, ("тип товару", "тип товара"))
    for kind, words in TYPES.items():
        if declared.casefold() in {kind.casefold(), words[0].casefold(), words[1].casefold()}:
            return kind
    for name in (field(offer, "name_ua"), field(offer, "name")):
        for kind, words in sorted(TYPES.items(), key=lambda kv: -len(kv[0])):
            for term in (kind, words[0], words[1]):
                if re.match(r"^" + re.escape(term) + r"(?=\s|$)", name, re.I):
                    return kind
    return None

def remove_type(name, kind):
    words = TYPES[kind]
    for term in sorted({kind, words[0], words[1]}, key=len, reverse=True):
        name = re.sub(r"^" + re.escape(term) + r"(?=\s|$)\s*", "", name, flags=re.I)
    return name

def extract_identity(offer, kind, params):
    brand = first(params, BRAND_KEYS)
    model = first(params, MODEL_KEYS)
    size = first(params, SIZE_KEYS)
    color = first(params, COLOR_KEYS)
    # Use the existing product identity only if it can be extracted safely.
    existing = field(offer, "name_ua") or field(offer, "name")
    existing = remove_type(existing, kind)
    existing = re.split(r"\s+[—–]\s+", existing)[0]
    existing = re.sub(r"\s+(?:розмір|размер)\s+\S+.*$", "", existing, flags=re.I)
    existing = clean(existing)
    if not brand:
        # V11 stores "brand in name" inside the existing title.
        brand = existing
    if brand and existing.casefold().startswith(brand.casefold()):
        rest = clean(existing[len(brand):])
        if rest and not model:
            model = rest
    # Avoid writing huge keyword-stuffed phrases as brands.
    if len(brand) > 55 or UNSAFE_UA.search(brand) or UNSAFE_RU.search(brand):
        return None
    return brand, model, size, color

def convert_color(color, lang):
    if not color:
        return ""
    word = color.casefold()
    if lang == "ua":
        return RU_TO_UA.get(word, color)
    return COLORS.get(word, color)

def unique(values):
    seen, result = set(), []
    for value in values:
        value = clean(value)
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
    return result

def create_title(kind, identity, lang):
    brand, model, size, color = identity
    typ, syn = (TYPES[kind][0], TYPES[kind][2]) if lang == "ua" else (TYPES[kind][1], TYPES[kind][3])
    parts = [typ.capitalize(), brand]
    if model and model.casefold() not in brand.casefold():
        parts.append(model)
    color_text = convert_color(color, lang)
    if color_text and not any(color_text.casefold() in x.casefold() for x in parts):
        parts.append(color_text)
    if size:
        parts.append(("розмір " if lang == "ua" else "размер ") + size)
    title = clean(" ".join(parts))
    if syn and len(title) < 70 and len(title + " — " + syn) <= 100:
        title += " — " + syn
    return title

def create_keywords(kind, identity, lang):
    brand, model, size, color = identity
    typ, syn = (TYPES[kind][0], TYPES[kind][2]) if lang == "ua" else (TYPES[kind][1], TYPES[kind][3])
    base = clean(f"{typ} {brand}")
    terms = [base]
    if model and model.casefold() not in brand.casefold():
        terms.append(clean(f"{base} {model}"))
    if size:
        terms.append(f"{base} {size}")
    if color:
        terms.append(f"{base} {convert_color(color, lang)}")
    if syn:
        terms.append(clean(f"{syn} {brand}"))
    return ", ".join(unique(terms)[:8])

# Only translate parameter labels with known exact equivalents.
PARAM_LABELS = {
    "матеріал": ("Матеріал", "Материал"),
    "материал": ("Матеріал", "Материал"),
    "склад": ("Склад", "Состав"),
    "состав": ("Склад", "Состав"),
    "сезон": ("Сезон", "Сезон"),
    "стать": ("Стать", "Пол"),
    "пол": ("Стать", "Пол"),
    "країна виробник": ("Країна виробництва", "Страна производства"),
    "страна производитель": ("Країна виробництва", "Страна производства"),
}
def description(title, kind, identity, params, offer, lang):
    brand, model, size, color = identity
    is_ua = lang == "ua"
    typ = TYPES[kind][0 if is_ua else 1]
    fields = [
        ("Тип товару" if is_ua else "Тип товара", typ),
        ("Модель", model),
        ("Розмір" if is_ua else "Размер", size),
        ("Колір" if is_ua else "Цвет", convert_color(color, lang)),
        ("Артикул", field(offer, "vendorCode") or first(params, ("артикул",))),
    ]
    # Only add supplier-provided values that do not need uncertain translation.
    for key, labels in PARAM_LABELS.items():
        value = params.get(key)
        if value:
            fields.append((labels[0 if is_ua else 1], value))
    fields = [(k, v) for k, v in fields if v]
    fields = list(dict(((k.casefold(), v.casefold()), (k, v)) for k, v in fields).values())
    heading = "Характеристики товару" if is_ua else "Характеристики товара"
    intro = (f"{typ.capitalize()} {brand} — товар із зазначеними нижче характеристиками."
             if is_ua else
             f"{typ.capitalize()} {brand} — товар с указанными ниже характеристиками.")
    # Do not assert fabric, authenticity, shipment speed or stock without proof.
    note = ("Перед замовленням звірте розмір та комплектацію з фотографіями й параметрами товару."
            if is_ua else
            "Перед заказом сверьте размер и комплектацию с фотографиями и параметрами товара.")
    rows = "".join(
        f"<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>"
        for k, v in fields
    )
    return (f"<h2>{html.escape(title)}</h2>"
            f"<p>{html.escape(intro)}</p>"
            f"<h3>{heading}</h3><ul>{rows}</ul>"
            f"<p>{html.escape(note)}</p>")

def process(offer):
    params = get_params(offer)
    kind = detect_type(offer, params)
    if not kind:
        return "unknown_type"
    identity = extract_identity(offer, kind, params)
    if identity is None:
        return "uncertain_identity"
    for lang, suffix in (("ua", "_ua"), ("ru", "")):
        title = create_title(kind, identity, lang)
        if len(title) > 100 or (UNSAFE_UA if lang == "ua" else UNSAFE_RU).search(title):
            return "mixed_language"
    for lang, suffix in (("ua", "_ua"), ("ru", "")):
        title = create_title(kind, identity, lang)
        set_field(offer, "name" + suffix, title)
        set_field(offer, "keywords" + suffix, create_keywords(kind, identity, lang))
        set_field(offer, "description" + suffix, description(title, kind, identity, params, offer, lang))
    return "updated"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", nargs="?", default="public/mydrop.xml")
    args = parser.parse_args()
    tree = etree.parse(args.xml, etree.XMLParser(resolve_entities=False, no_network=True))
    offers = tree.findall(".//offer")
    counts = Counter(process(offer) for offer in offers)
    tree.write(args.xml, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"SEO V13: total={len(offers)}; " +
          "; ".join(f"{key}={value}" for key, value in sorted(counts.items())))


# V13: safer fallback for products with missing or unreliable brand fields.
# Never rewrite an item if a product identity cannot be recovered confidently.
COMMON_STOP = re.compile(r"\b(?:для|повсякденних|повседневных|образів|образов|кофта|толстовка|капюшоном|розмір|размер)\b", re.I)
BRAND_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9.&'-]{1,30}$")

def fallback_identity(offer, kind, params):
    brand = first(params, BRAND_KEYS)
    model = first(params, MODEL_KEYS)
    size = first(params, SIZE_KEYS)
    color = first(params, COLOR_KEYS)
    source = field(offer, "name_ua") or field(offer, "name")
    source = remove_type(source, kind)
    source = re.split(r"\s+[—–]\s+", source)[0]
    source = re.sub(r"\s+(?:розмір|размер)\s+[^ ]+.*$", "", source, flags=re.I)
    source = clean(source)
    if not brand:
        tokens = source.split()
        if tokens and BRAND_TOKEN.fullmatch(tokens[0]):
            brand = tokens[0]
            if len(tokens) > 1 and not model:
                rest = clean(" ".join(tokens[1:]))
                if rest and not COMMON_STOP.search(rest) and len(rest) <= 35:
                    model = rest
        else:
            return None
    if COMMON_STOP.search(brand) or len(brand) > 40:
        return None
    if model and (COMMON_STOP.search(model) or len(model) > 50):
        model = ""
    return brand, model, size, color

def process_v13(offer):
    params = get_params(offer)
    kind = detect_type(offer, params)
    if not kind:
        return "unknown_type"
    identity = extract_identity(offer, kind, params)
    if identity is None or any(
        (UNSAFE_UA if lang == "ua" else UNSAFE_RU).search(create_title(kind, identity, lang))
        for lang in ("ua", "ru")
    ):
        identity = fallback_identity(offer, kind, params)
    if identity is None:
        return "uncertain_identity"
    proposed = {}
    for lang, suffix in (("ua", "_ua"), ("ru", "")):
        title = create_title(kind, identity, lang)
        if (UNSAFE_UA if lang == "ua" else UNSAFE_RU).search(title):
            return "mixed_language"
        if len(title) < 8 or len(title) > 100:
            return "invalid_title"
        proposed["name" + suffix] = title
        proposed["keywords" + suffix] = create_keywords(kind, identity, lang)
        proposed["description" + suffix] = description(title, kind, identity, params, offer, lang)
    for key, value in proposed.items():
        set_field(offer, key, value)
    return "updated"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", nargs="?", default="public/mydrop.xml")
    args = parser.parse_args()
    tree = etree.parse(args.xml, etree.XMLParser(resolve_entities=False, no_network=True))
    offers = tree.findall(".//offer")
    rows = []
    for offer in offers:
        before = field(offer, "name_ua") or field(offer, "name")
        result = process_v13(offer)
        rows.append({"offer_id": offer.get("id", ""), "status": result,
                     "source_title": before, "result_title_ua": field(offer, "name_ua")})
    counts = Counter(row["status"] for row in rows)
    # Write audit before replacing the XML; no products are removed.
    audit = Path(args.xml).with_name("seo_v13_audit.csv")
    with audit.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else
                                ["offer_id", "status", "source_title", "result_title_ua"])
        writer.writeheader()
        writer.writerows(rows)
    tree.write(args.xml, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    print(f"SEO V13: total={len(offers)}; " +
          "; ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"Audit report: {audit}")



# V14: corrections validated against the uploaded 630-offer XML.
# The original supplier's commercial fields and XML structure are not changed.
COLOR_VARIANTS = {
    'чорний': 'черный', 'сірий': 'серый', 'білий': 'белый',
    'червоний': 'красный', 'бежевий': 'бежевый',
    'зелений': 'зеленый', 'синій': 'синий',
    'коричневий': 'коричневый', 'рожевий': 'розовый',
    'блакитний': 'голубой', 'жовтий': 'желтый',
}
REVERSE_COLORS = {v:k for k,v in COLOR_VARIANTS.items()}
COLOR_RE = re.compile(r'(?<!\w)(' + '|'.join(map(re.escape, sorted(set(COLOR_VARIANTS)|set(REVERSE_COLORS), key=len, reverse=True))) + r')(?!\w)', re.I)
NOISE_RE = re.compile(r'\s*[—–]\s*.*$')
SIZE_RE = re.compile(r'\s+(?:розмір|размер)\s+.*$', re.I)


def normalize_colors(s, lang):
    def repl(m):
        w=m.group(0).lower()
        return (REVERSE_COLORS.get(w,w) if lang=='ua' else COLOR_VARIANTS.get(w,w))
    return COLOR_RE.sub(repl,s)


def classify(offer, params):
    declared=first(params,('тип товару','тип товара'))
    if declared:
        for kind, words in TYPES.items():
            if declared.casefold() in {kind.casefold(), words[0].casefold(),words[1].casefold()}:
                return kind
    return detect_type(offer,params)


def identity_v14(offer,kind,params):
    ua=field(offer,'name_ua') or field(offer,'name')
    ru=field(offer,'name')
    size=first(params,SIZE_KEYS)
    color=first(params,COLOR_KEYS)
    brand=first(params,BRAND_KEYS)
    model=first(params,MODEL_KEYS)
    core=clean(SIZE_RE.sub('',NOISE_RE.sub('',remove_type(ua,kind))))
    core=re.sub(r'^(?:розмір|размер)\b.*$', '', core, flags=re.I).strip()
    # Remove supplier colour from the product identity, not from the size or SKU.
    if color:
        for c in {color,normalize_colors(color,'ua'),normalize_colors(color,'ru')}:
            core=re.sub(r'(?<!\w)'+re.escape(c)+r'(?!\w)','',core,flags=re.I)
        core=clean(core)
    # Colours are sometimes supplied inside a size field, e.g. '36-41 Червоний'.
    if size:
        m=COLOR_RE.search(size)
        if m and not color:
            color=m.group(0)
            size=clean(size[:m.start()]+size[m.end():])
        elif m:
            size=clean(COLOR_RE.sub('',size))
    # Colour is occasionally placed in the size field alone.
    if size and COLOR_RE.fullmatch(size):
        if not color: color=size
        size=''
    if size in ('-', '—', '–', 'немає', 'нет'):
        size=''
    if not size:
        size=clean(first(params,('размер',)))
    if not size:
        m=re.search(r'\b(?:розмір|размер)\s+([^—–]+)',ua,re.I)
        if m: size=clean(m.group(1))
    if size and size.casefold() in ('універсальний','универсальный'):
        size='One size' if 'one size' in ua.lower() else size
    # Existing brand parameter is more trustworthy than guessing from title.
    if brand:
        if core.casefold().startswith(brand.casefold()):
            tail=clean(core[len(brand):])
            if tail and not model: model=tail
    elif core:
        brand=core
    # No brand? Use category as a legitimate generic product title.
    if not brand:
        brand=''
    if brand.casefold() in ('розмір','размер') or len(brand)>65:
        brand=''
    if model:
        model=clean(model.strip('() '))
    if brand and model and model.casefold() in brand.casefold():
        model=''
    if brand and model and brand.casefold() in model.casefold():
        model=''
    # The Cyrillic transliteration in parentheses is a synonym, not a model.
    if model and re.fullmatch(r'[А-Яа-яІіЇїЄєҐґ\s-]+',model):
        model=''
    # Product title from V13 can include old colour/size in a pseudo-brand.
    if not first(params,BRAND_KEYS):
        brand=clean(re.sub(r'\s+(?:розмір|размер)\b.*$','',brand,flags=re.I))
    return (brand,model,size,color)


def make_title_v14(kind, identity, lang):
    brand,model,size,color=identity
    typ=TYPES[kind][0 if lang=='ua' else 1]
    syn=TYPES[kind][2 if lang=='ua' else 3]
    pieces=[typ.capitalize()]
    if brand: pieces.append(normalize_colors(brand,lang))
    if model and model.casefold() not in brand.casefold():pieces.append(normalize_colors(model,lang))
    if color:
        c=normalize_colors(color,lang)
        if not any(re.search(r'(?<!\w)'+re.escape(c)+r'(?!\w)',x,re.I) for x in pieces):pieces.append(c)
    if size:pieces.append(('розмір ' if lang=='ua' else 'размер ')+normalize_colors(size,lang))
    title=clean(' '.join(pieces))
    if syn and len(title)<65 and len(title+' — '+syn)<=100:
        title+=' — '+syn
    return title[:100].rstrip(' —') if len(title)>100 else title


def process_v14(offer):
    params=get_params(offer)
    kind=classify(offer,params)
    if not kind:return 'unknown_type'
    identity=identity_v14(offer,kind,params)
    brand,model,size,color=identity
    proposed={}
    for lang,suffix in (('ua','_ua'),('ru','')):
        title=make_title_v14(kind,identity,lang)
        if len(title)<5 or (UNSAFE_UA if lang=='ua' else UNSAFE_RU).search(title):
            return 'review_language'
        proposed['name'+suffix]=title
        # Avoid keyword stuffing; include only grounded attributes.
        proposed['keywords'+suffix]=create_keywords(kind,identity,lang)
        proposed['description'+suffix]=description(title,kind,identity,params,offer,lang)
    for key,value in proposed.items():set_field(offer,key,value)
    return 'updated' if brand else 'generic_no_brand'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('xml',nargs='?',default='public/mydrop.xml')
    args=parser.parse_args()
    tree=etree.parse(args.xml,etree.XMLParser(resolve_entities=False,no_network=True))
    offers=tree.findall('.//offer')
    protected=('price','currencyId','categoryId','picture','vendor','vendorCode','available','quantity_in_stock','url')
    snapshots=[(dict(o.attrib),[(k,tuple(x.text for x in o.findall(k))) for k in protected],[(p.get('name'),p.text) for p in o.findall('param')]) for o in offers]
    rows=[]
    for o in offers:
        old=field(o,'name_ua')
        status=process_v14(o)
        rows.append({'offer_id':o.get('id',''),'status':status,'source_title':old,'result_title_ua':field(o,'name_ua')})
    for o,s in zip(offers,snapshots):
        assert dict(o.attrib)==s[0]
        assert [(k,tuple(x.text for x in o.findall(k))) for k in protected]==s[1]
        # V14 does not modify any existing parameters.
        assert [(p.get('name'),p.text) for p in o.findall('param')]==s[2]
    audit=Path(args.xml).with_name('seo_v14_audit.csv')
    with audit.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    tree.write(args.xml,encoding='UTF-8',xml_declaration=True,pretty_print=True)
    counts=Counter(x['status'] for x in rows)
    print('SEO V14: total='+str(len(rows))+'; '+'; '.join(f'{k}={v}' for k,v in sorted(counts.items())))
    print('Audit report:',audit)

if __name__=='__main__':main()
