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
