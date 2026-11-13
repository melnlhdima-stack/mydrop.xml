from lxml import etree
from collections import Counter
import re, math, html, os, urllib.request
from pathlib import Path
OUT='public/mydrop.xml'
Path('public').mkdir(exist_ok=True)
source_url=os.environ.get('MYDROP_FEED_URL')
if not source_url:
 raise RuntimeError('Set MYDROP_FEED_URL GitHub Actions secret')
request=urllib.request.Request(source_url,headers={'User-Agent':'Mozilla/5.0 PromAutoFeed/1.0'})
with urllib.request.urlopen(request,timeout=120) as response:
 source_xml=response.read()
if not source_xml.lstrip().startswith(b'<?xml') and not source_xml.lstrip().startswith(b'<yml_catalog'):
 raise ValueError('Supplier did not return XML')
tree=etree.ElementTree(etree.fromstring(source_xml)); root=tree.getroot(); offers=root.find('.//offers')
cats={c.get('id'):(c.text or '') for c in root.findall('.//categories/category')}
family={'170191':'футболка','170192':'шорти','170183':'шапка','170182':'кепка','170231':'пуховик','170196':'костюм','170194':'джинси','170193':'штани','170195':'кофта','170198':'куртка','170197':'жилетка','170250':'худі','170188':'гаманець','170184':'ремінь','170190':'шнурки','170186':'підвіска','170311':'рюкзак','170755':'рюкзак','170756':'сумка'}
ru={'футболка':'футболка','шорти':'шорты','шапка':'шапка','кепка':'кепка','пуховик':'пуховик','костюм':'костюм','джинси':'джинсы','штани':'штаны','кофта':'кофта','куртка':'куртка','жилетка':'жилетка','худі':'худи','гаманець':'кошелек','ремінь':'ремень','шнурки':'шнурки','підвіска':'подвеска','рюкзак':'рюкзак','сумка':'сумка','барсетка':'барсетка','шкарпетки':'носки'}
stop={'чоловічий','жіночий','брендовий','стильний','купити','оригінал','оригинал'}
stat=Counter()
def text_set(e,k,val):
 x=e.find(k)
 if x is None:x=etree.SubElement(e,k)
 x.text=str(val)
def type_of(o):
 n=(o.findtext('name') or '').lower();c=o.findtext('categoryId') or ''
 for k,t in [('пуховик','пуховик'),('куртка','куртка'),('вітровк','вітровка'),('олімпійк','олімпійка'),('зипк','кофта'),('зіпк','кофта'),('жилет','жилетка'),('худі','худі'),('худи','худі'),('світшот','світшот'),('свитшот','світшот'),('барсет','барсетка'),('шкарпет','шкарпетки'),('сумка','сумка'),('шапка','шапка'),('панама','панама'),('кепка','кепка'),('шорти','шорти'),('футболка','футболка'),('костюм','костюм'),('джинси','джинси'),('штани','штани'),('рюкзак','рюкзак')]:
  if k in n:return t
 if c in ['170313','170314','170315','170317','170318','170312']:return 'барсетка'
 if c in ['170322','170323','170321']:return 'шкарпетки'
 return family.get(c,'аксесуар')
def kind(o,t):
 c=o.findtext('categoryId') or ''
 if t=='пуховик':return 'puffer',19,350
 if c=='170196' or t=='костюм':return 'suit',19,250
 if t=='шапка' or c=='170183':return 'hat',17,200
 if c in ('170191','170192') or t in ('футболка','шорти'):return 'summer',18,300
 if t in ('куртка','вітровка','олімпійка') or c=='170198':return 'jacket',19,250
 return 'other',18,250
for o in list(offers):
 t=type_of(o); k,fee,profit=kind(o,t)
 try:base=float((o.findtext('price') or '').replace(',','.'));assert base>0
 except:offers.remove(o);stat['excluded_no_price']+=1;continue
 # Rounding upward preserves target after percent fee, assuming no other expenses.
 price=math.ceil((base+profit)/(1-fee/100))
 name=' '.join((o.findtext('name') or '').split()).strip()
 # Remove initial category term only to avoid duplicates.
 remainder=re.sub(r'^(?:пуховик\s*[-–]?\s*жилетка|пуховик|куртка|вітровка|олімпійка|худі|худи|зіпка|зипка|футболка|шорти|шапка|кепка|панама|костюм|джинси|штани|штаны|кофта|жилетка|сумка|рюкзак|барсетка|шкарпетки|гаманець|ремінь|шнурки|підвіска)\s*[-–]?\s*','',name,flags=re.I).strip()
 if not remainder:remainder=name
 if t=='пуховик' and 'жилетка' in name.lower():t='пуховик-жилетка'
 label={'штани':'Штани','худі':'Худі','сумка':'Сумка','шкарпетки':'Шкарпетки','пуховик-жилетка':'Пуховик-жилетка'}.get(t,t.capitalize())
 size=next((p.text.strip() for p in o.findall('param') if p.get('name','').lower() in ('размер','розмір') and p.text and p.text.strip()!='-'),None)
 code=o.findtext('vendorCode') or o.get('id')
 title=f'{label} {remainder}'
 if size and not re.search(r'нюанс',size,re.I):title+=f' — розмір {size}'
 if size and re.search(r'нюанс',size,re.I):title+=f' — {size} (є нюанс)'
 title=f'{title} | арт. {code}'
 title=re.sub(r'\s+',' ',title).strip()
 text_set(o,'name',title[:245]);text_set(o,'price',price)
 # Only existing, explicitly supplied properties are used.
 properties=[('Тип товару',t),('Артикул',code)]
 if size:properties.append(('Розмір',size))
 if 'нюанс' in (size or '').lower():properties.append(('Стан','Є нюанс — уточніть перед замовленням'))
 for n,v in properties:
  if not any(p.get('name')==n for p in o.findall('param')):
   etree.SubElement(o,'param',name=n).text=v
 # Keywords reflect supplied product and category, not unverified features.
 base_terms=[f'{t} {remainder}',f'купити {t} {remainder}',f'{t} {remainder} україна',f'{t} {remainder} ціна',f'{remainder} {t}',f'{t} {remainder} замовити',f'{t} {remainder} онлайн',f'{t} {remainder} пром',f'{t} {remainder} доставка']
 if size:base_terms.extend([f'{t} {remainder} {size}',f'{remainder} розмір {size}'])
 base_terms += [name, f'{t} {remainder} каталог']
 r=ru.get(t,t)
 ru_terms=[f'{r} {remainder}',f'купить {r} {remainder}',f'{r} {remainder} украина',f'{r} {remainder} цена',f'{remainder} {r}',f'{r} {remainder} заказать',f'{r} {remainder} доставка']
 if size:ru_terms.append(f'{r} {remainder} {size}')
 def join_unique(xs):
  out=[];seen=set()
  for x in xs:
   x=' '.join(x.split());q=x.casefold()
   if q not in seen and len(x)>2:out.append(x);seen.add(q)
  return ', '.join(out)[:1024].rstrip(' ,')
 text_set(o,'keywords_ua',join_unique(base_terms));text_set(o,'keywords',join_unique(ru_terms))
 desc=(f'<h2>{html.escape(label)} {html.escape(remainder)}</h2>'
       f'<p>Шукаєте {html.escape(t)} у стилі {html.escape(remainder)}? Ця модель представлена в нашому каталозі одягу та аксесуарів. '
       f'Перед оформленням замовлення перегляньте фотографії, доступні варіанти та уточніть деталі, які для вас важливі.</p>'
       f'<h3>Інформація про товар</h3><ul>'
       f'<li>Найменування: {html.escape(name)}.</li>'
       f'<li>Категорія: {html.escape(cats.get(o.findtext("categoryId"),t))}.</li>'
       f'<li>Артикул для уточнення: {html.escape(code)}.</li>'
       +(f'<li>Розмір у цій позиції: {html.escape(size)}.</li>' if size else '')
       +f'<li>Зовнішній вигляд та комплектацію звіряйте з фотографіями товару.</li></ul>'
       f'<h3>Як підібрати та замовити</h3><p>Перед покупкою рекомендуємо перевірити розмір за замірами, '
       f'уточнити склад матеріалу, посадку й актуальну наявність. Якщо маєте запитання щодо моделі, '
       f'вкажіть артикул {html.escape(code)} — це допоможе швидше знайти потрібний варіант.</p>'
       f'<h3>Чому варто переглянути цю модель</h3><p>Зручний пошук за назвою та артикулом, '
       f'фотографії від постачальника й можливість уточнити характеристики перед замовленням. '
       f'Обирайте свій варіант і оформлюйте покупку через Prom.ua.</p>'
       +(f'<p><strong>Увага:</strong> постачальник позначив цей розмір як «нюанс». Перед оплатою обов’язково уточніть стан товару.</p>' if size and 'нюанс' in size.lower() else ''))
 text_set(o,'description',desc)
 stat[k]+=1
stat['total']=sum(v for k,v in stat.items() if k!='excluded_no_price')
tree.write(OUT,encoding='utf-8',xml_declaration=True,pretty_print=True)
print(stat,OUT)
