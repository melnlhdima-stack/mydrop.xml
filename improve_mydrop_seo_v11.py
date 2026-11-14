#!/usr/bin/env python3
"""MyDrop SEO V11: bilingual XML postprocessor. Run AFTER build_mydrop_github_SEO_v9.py.
Only edits name, name_ua, keywords, keywords_ua, description, description_ua.
Never invents material, fit, season, origin, authenticity or availability.
"""
import argparse
import html
import re
from collections import Counter
from lxml import etree

TYPES = {
 'Худі':('худі','худи','кофта з капюшоном','кофта с капюшоном'),
 'Штани':('штани','штаны','брендові штани','брендовые штаны'),
 'Джинси':('джинси','джинсы','джинсові штани','джинсовые брюки'),
 'Куртка':('куртка','куртка','',''),
 'Футболка':('футболка','футболка','',''),
 'Костюм':('костюм','костюм','комплект одягу','комплект одежды'),
 'Жилетка':('жилетка','жилетка','жилет','жилет'),
 'Шорти':('шорти','шорты','',''),
 'Рюкзак':('рюкзак','рюкзак','',''),
 'Сумка':('сумка','сумка','',''),
 'Кепка':('кепка','кепка','бейсболка','бейсболка'),
 'Шапка':('шапка','шапка','',''),
 'Шкарпетки':('шкарпетки','носки','',''),
 'Олімпійка':('олімпійка','олимпийка','кофта на блискавці','кофта на молнии'),
 'Кофта на блискавці':('кофта на блискавці','кофта на молнии','',''),
 'Кофта':('кофта','кофта','',''),
 'Світшот':('світшот','свитшот','',''),
 'Пуховик':('пуховик','пуховик','',''),
 'Кросівки':('кросівки','кроссовки','взуття','обувь'),
 'Шльопанці':('шльопанці','шлепанцы','',''),
 'Сорочка':('сорочка','рубашка','',''),
 'Поло':('поло','поло','',''),
 'Спідниця':('спідниця','юбка','',''),
 'Сукня':('сукня','платье','',''),
 'Лонгслів':('лонгслів','лонгслив','',''),
 'Кардиган':('кардиган','кардиган','',''),
}
COLORS = {'чорний':'черный','білий':'белый','сірий':'серый','синій':'синий','зелений':'зеленый','червоний':'красный','коричневий':'коричневый','бежевий':'бежевый','рожевий':'розовый','жовтий':'желтый','блакитний':'голубой','фіолетовий':'фиолетовый','помаранчевий':'оранжевый'}
REVERSE_COLORS={v:k for k,v in COLORS.items()}
FILLER=re.compile(r'\s*[—–-]\s*(?:кофта худі|толстовка худі|кофта худи|толстовка|для повсякденних образів|для повседневных образов|для щоденного гардероба|для повседневного гардероба).*$',re.I)

def clean(s): return re.sub(r'\s+',' ',html.unescape(s or '')).strip()
def put(o,k,v):
 e=o.find(k)
 if e is None:e=etree.SubElement(o,k)
 e.text=v

def uniq(items):
 seen=set();out=[]
 for x in items:
  x=clean(x); key=x.casefold()
  if x and key not in seen:seen.add(key);out.append(x)
 return out

def parammap(o):
 return {clean(p.get('name')).casefold():clean(p.text) for p in o.findall('param')}

def classify(o,p):
 kind=p.get('тип товару') or p.get('тип товара') or ''
 if kind in TYPES:return kind
 name=clean(o.findtext('name_ua') or o.findtext('name'))
 for k,(ua,ru,*_) in sorted(TYPES.items(),key=lambda kv:-len(kv[0])):
  if re.match(r'^'+re.escape(k)+r'\b',name,re.I) or re.match(r'^'+re.escape(ua)+r'\b',name,re.I) or re.match(r'^'+re.escape(ru)+r'\b',name,re.I):return k
 return None

def original_model(o,kind,brand,color,size):
 title=clean(o.findtext('name_ua') or o.findtext('name'))
 title=FILLER.sub('',title)
 title=re.sub(r'\s+(?:розмір|размер)\s+.*$', '',title,flags=re.I)
 for t in [kind,TYPES[kind][0],TYPES[kind][1]]:
  title=re.sub(r'^'+re.escape(t)+r'\s+', '',title,flags=re.I)
 if brand:title=re.sub(r'^'+re.escape(brand)+r'\b\s*','',title,flags=re.I)
 title=re.sub(r'\([^)]*\)','',title)
 if color:
  for c in {color,COLORS.get(color.lower(),''),REVERSE_COLORS.get(color.lower(),'')} - {''}:
   title=re.sub(r'\b'+re.escape(c)+r'\b','',title,flags=re.I)
 title=clean(title.strip(' ,—–-'))
 # Avoid inheriting SEO junk from previous generator.
 title=re.sub(r'\b(?:для повсякденних|для повседневных|толстовка худі|толстовка худи)\b.*$','',title,flags=re.I).strip()
 return title if len(title)<70 else ''

def process(o):
 p=parammap(o);kind=classify(o,p)
 if not kind:return False
 ua,ru,ua_syn,ru_syn=TYPES[kind]
 brand=clean(p.get('бренд у назві') or p.get('бренд в названии') or '')
 size=clean(p.get('розмір') or p.get('размер') or '')
 color=clean(p.get('колір') or p.get('цвет') or '')
 cu=REVERSE_COLORS.get(color.casefold(),color);cr=COLORS.get(color.casefold(),color)
 model=original_model(o,kind,brand,color,size)
 # Preserve existing brand when param absent, but do not infer an unknown brand.
 if not brand:
  src=FILLER.sub('',clean(o.findtext('name_ua') or o.findtext('name')))
  src=re.sub(r'\s+(?:розмір|размер)\s+.*$','',src,flags=re.I)
  src=re.sub(r'^'+re.escape(ua)+r'\s+','',src,flags=re.I)
  src=re.sub(r'^'+re.escape(ru)+r'\s+','',src,flags=re.I)
  brand=clean(src)
  model=''
 # Avoid color/size twice.
 def title(lang):
  typ=ua if lang=='ua' else ru; col=cu if lang=='ua' else cr
  parts=[typ.capitalize(),brand]
  if model and model.casefold() not in brand.casefold():parts.append(model)
  if col and not any(col.casefold() in v.casefold() for v in parts):parts.append(col)
  if size:parts.append(('розмір ' if lang=='ua' else 'размер ')+size)
  name=clean(' '.join(parts))
  synonym=ua_syn if lang=='ua' else ru_syn
  # Add only a meaningful category synonym, never padding filler to reach a quota.
  if synonym and len(name)<70 and synonym.casefold() not in name.casefold():
   candidate=name+' — '+synonym
   if len(candidate)<=100:name=candidate
  return name
 tu=title('ua');tr=title('ru')
 def keywords(lang):
  typ=ua if lang=='ua' else ru; syn=ua_syn if lang=='ua' else ru_syn
  col=cu if lang=='ua' else cr
  base=clean(' '.join(x for x in [typ,brand] if x))
  out=[base]
  if syn and brand:out.append(syn+' '+brand)
  if model and brand:out.extend([base+' '+model,brand+' '+model])
  if col:out.append(base+' '+col)
  if size:out.append(base+' '+size)
  # Keep specific established brand spelling variants, without importing old language-mixed junk.
  old=clean(o.findtext('keywords_ua' if lang=='ua' else 'keywords'))
  for item in old.split(','):
   item=clean(item)
   if not item or len(item)>90:continue
   if lang=='ua' and re.search(r'\b(?:толстовка|худи|штаны|джинсы|шорты|размер)\b',item,re.I):continue
   if lang=='ru' and re.search(r'\b(?:худі|штани|джинси|шорти|розмір|кофта худі)\b',item,re.I):continue
   if brand and brand.casefold() not in item.casefold():continue
   out.append(item)
  return ', '.join(uniq(out)[:12])
 article=clean(o.findtext('vendorCode') or p.get('артикул') or '')
 def desc(lang):
  isua=lang=='ua'; typ=ua if isua else ru;name=tu if isua else tr
  fields=[]
  if brand:fields.append(('Бренд у назві' if isua else 'Бренд в названии',brand))
  fields.append(('Тип товару' if isua else 'Тип товара',typ))
  if model:fields.append(('Модель' if isua else 'Модель',model))
  if size:fields.append(('Розмір' if isua else 'Размер',size))
  if color:fields.append(('Колір' if isua else 'Цвет',cu if isua else cr))
  if article:fields.append(('Артикул',article))
  # All other supplier parameters preserved in XML; do not guess their meaning here.
  intro=(f'{typ.capitalize()} {brand}'.strip()+'. Доступні параметри конкретного варіанта наведено нижче.' if isua else f'{typ.capitalize()} {brand}'.strip()+'. Параметры выбранного варианта указаны ниже.')
  lis=''.join(f'<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>' for k,v in fields)
  note=('Перевірте розмір і фотографії товару перед оформленням замовлення.' if isua else 'Проверьте размер и фотографии товара перед оформлением заказа.')
  return f'<h2>{html.escape(name)}</h2><p>{html.escape(intro)}</p><h3>{"Характеристики" if isua else "Характеристики"}</h3><ul>{lis}</ul><p>{html.escape(note)}</p>'
 put(o,'name_ua',tu);put(o,'name',tr)
 put(o,'keywords_ua',keywords('ua'));put(o,'keywords',keywords('ru'))
 put(o,'description_ua',desc('ua'));put(o,'description',desc('ru'))
 return True

def main():
 ap=argparse.ArgumentParser();ap.add_argument('path',nargs='?',default='public/mydrop.xml');a=ap.parse_args()
 tree=etree.parse(a.path,etree.XMLParser(resolve_entities=False,no_network=True,huge_tree=True))
 offers=tree.findall('.//offer');done=sum(process(o) for o in offers)
 tree.write(a.path,encoding='UTF-8',xml_declaration=True,pretty_print=True)
 print(f'SEO V11: processed {done}/{len(offers)} offers; unrecognized {len(offers)-done}')
if __name__=='__main__':main()
