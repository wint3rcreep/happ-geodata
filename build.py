#!/usr/bin/env python3
"""Build minimal Happ geodata. No credentials or client data used."""
import argparse, datetime, hashlib, ipaddress, json, os, pathlib, re, shutil, tempfile, urllib.request
BASE='https://raw.githubusercontent.com/runetfreedom/russia-v2ray-rules-dat/release/'
GEO='https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Categories/geoblock.lst'
BEEMOOV='''beemoov.com beemoov.net eldarya.com eldarya.fr eldarya.ru amoursucre.com amoursucre-newgen.com mycandylove.com mycandylove-newgen.com moonlightlovers.com moonlightlovers.com.br moonlightlovers.de moonlightlovers.es moonlightlovers.fr moonlightlovers.pl moonlightlovers.ru ma-bimbo.com lesecretdhenri.com'''.split()
def varint(n):
 b=bytearray()
 while n>127:b.append((n&127)|128);n>>=7
 b.append(n);return bytes(b)
def readvar(b,i):
 n=s=0
 for _ in range(10):
  if i>=len(b):raise ValueError('truncated varint')
  x=b[i];i+=1;n|=(x&127)<<s
  if x<128:return n,i
  s+=7
 raise ValueError('varint overflow')
def fields(b):
 i=0
 while i<len(b):
  t,i=readvar(b,i);wire=t&7
  if wire==0:v,i=readvar(b,i)
  elif wire==2:
   n,i=readvar(b,i)
   if i+n>len(b):raise ValueError('truncated bytes')
   v=b[i:i+n];i+=n
  elif wire in (1,5):
   n=8 if wire==1 else 4
   if i+n>len(b):raise ValueError('truncated fixed')
   v=b[i:i+n];i+=n
  else:raise ValueError('unsupported wire')
  if t>>3==0:raise ValueError('invalid field zero')
  yield t>>3,v
def blob(k,b):return varint(k*8+2)+varint(len(b))+b
def categories(b):
 out={}
 for k,v in fields(b):
  if k!=1:raise ValueError('unexpected top field')
  name=next(x.decode().lower() for n,x in fields(v) if n==1)
  if name in out:raise ValueError('duplicate category')
  out[name]=v
 return out
def domains(g):
 out=[]
 for k,v in fields(g):
  if k==2:
   f=dict(fields(v));out.append((f.get(1,0),f[2].decode()))
 return out
def group(name,ds):
 return blob(1,name.upper().encode())+b''.join(blob(2,varint(8)+varint(2)+blob(2,d.encode())) for d in ds)
def fetch(u):
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'homelab-happ-geodata/1.0'}),timeout=90) as r:
  b=r.read(120_000_001)
 if len(b)>120_000_000:raise ValueError('oversize upstream')
 return b
def build(root):
 root=pathlib.Path(root);root.mkdir(parents=True,exist_ok=True)
 # Stage everything; only a validated complete release becomes current.
 tmp=pathlib.Path(tempfile.mkdtemp(prefix='.build-',dir=root))
 try:
  raw=fetch(BASE+'geosite.dat');cats=categories(raw)
  blocked=domains(cats['ru-blocked']);private=domains(cats['private'])
  if len(blocked)<1000 or not private:raise ValueError('unexpected upstream cardinality')
  text=fetch(GEO).decode();ds=[]
  for l in text.splitlines():
   d=l.split('#',1)[0].strip().lower().rstrip('.')
   if not d:continue
   if not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9-]+',d):raise ValueError('invalid domain '+d)
   ds.append(d)
  ds=sorted(set(ds))
  if not 100<=len(ds)<=10000:raise ValueError('unexpected geoblock count')
  # Keep categories independent for auditability, count exact overlap only.
  exact={d for t,d in blocked if t==2}
  overlap=sorted(exact&set(ds))
  output=b''.join(blob(1,g) for g in [cats['private'],cats['ru-blocked'],group('geo-block',ds),group('beemoov',sorted(set(BEEMOOV)))])
  parsed=categories(output)
  assert set(parsed)=={'private','ru-blocked','geo-block','beemoov'}
  assert domains(parsed['geo-block'])==[(2,d) for d in ds]
  assert domains(parsed['ru-blocked'])==blocked
  ip=fetch(BASE+'geoip.dat');ips=categories(ip)
  if 'private' not in ips or 'ru' not in ips:raise ValueError('geoip missing required categories')
  for _,g in ips.items():
   for k,v in fields(g):
    if k==2:
     f=dict(fields(v));address=ipaddress.ip_address(f[1]);prefix=f.get(2,0)
     if prefix>address.max_prefixlen:raise ValueError('invalid CIDR')
  manifest={'built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{'geosite':BASE+'geosite.dat','geoip':BASE+'geoip.dat','geoblock':GEO},'counts':{'ru-blocked':len(blocked),'private':len(private),'geo-block':len(ds),'beemoov':len(BEEMOOV)},'exact_suffix_overlap_geoblock_ru_blocked':len(overlap),'overlap_examples':overlap[:20],'files':{}}
  for name,b in [('geosite.dat',output),('geoip.dat',ip)]:
   (tmp/name).write_bytes(b);manifest['files'][name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  (tmp/'manifest.json').write_text(json.dumps(manifest,indent=2))
  release=root/('release-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
  os.rename(tmp,release)
  link=root/'.current.new';link.symlink_to(release.name);os.replace(link,root/'current')
  print(json.dumps(manifest,ensure_ascii=False))
 finally:
  if tmp.exists():shutil.rmtree(tmp)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();build(a.root)
