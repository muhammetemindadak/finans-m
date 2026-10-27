#!/usr/bin/env python3
"""Fetch a Turkish gram-gold bid quote; preserve the last valid file on failure."""
import json, datetime, pathlib, urllib.request
UTC=datetime.timezone.utc
now=datetime.datetime.now(UTC)
headers={'User-Agent':'FinansimGoldUpdater/2.5 (+GitHub Actions)','Accept':'application/json'}

def get(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=18) as response:
        return json.load(response)

def check(value,when,source,stale=False):
    price=float(value)
    if not 100 < price < 1000000 or stale: raise ValueError('invalid or stale quote')
    stamp=datetime.datetime.fromisoformat(str(when).replace('Z','+00:00'))
    if stamp.tzinfo is None: raise ValueError('timestamp missing timezone')
    age=(now-stamp).total_seconds()
    if age < -600 or age > 90*60: raise ValueError(f'old quote ({round(age/60)} minutes)')
    return {'bid':price,'updatedAt':stamp.isoformat(),'source':source}

errors=[];quote=None
try:
    d=get('https://altingrafigi.com/api/v1/prices')
    rows=d.get('data',[])
    row=next((r for r in rows if r.get('category','').upper()=='GRAM ALTIN' and 'gram' in r.get('name','').lower()),None)
    if row is None: row=next((r for r in rows if 'gram altın' in r.get('name','').lower()),None)
    if row is None: raise ValueError('gram altın not found')
    quote=check(row['bid'],row.get('timestamp') or d.get('updatedAt'),'Altın Grafiği')
except Exception as e: errors.append('Altın Grafiği: '+str(e))
if quote is None:
    try:
        d=get('https://raw.githubusercontent.com/MehmetAkgul/currency-api-tr/main/v1/currencies/try-full.json')
        row=d['try']['xau_gram']
        quote=check(row['bid'],row.get('updated_at') or d.get('updated_at'),'currency-api-tr',d.get('is_stale',False))
    except Exception as e: errors.append('currency-api-tr: '+str(e))
if quote is None:
    print('No fresh quote; existing gold.json left unchanged. '+ ' | '.join(errors))
else:
    quote['checkedAt']=now.isoformat()
    pathlib.Path('gold.json').write_text(json.dumps(quote,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated gold.json:',quote)
