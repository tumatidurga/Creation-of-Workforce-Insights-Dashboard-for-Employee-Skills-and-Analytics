from pathlib import Path
from pymongo import MongoClient
from datetime import datetime
repo = Path(r'D:\infosys springboard internship docs\workforce-management-automation-system')
vals = {}
for line in (repo / '.env').read_text(encoding='utf-8', errors='ignore').splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")
client = MongoClient(vals['MONGODB_URL'], serverSelectionTimeoutMS=10000)
db = client[vals['DATABASE_NAME']]
# counts
accounts_count = db.user_accounts.count_documents({})
with_hash = db.user_accounts.count_documents({'passwordHash': {'$exists': True, '$ne': None, '$ne': ''}})
# bcrypt-like
bcrypt_like = 0
plaintext_like = 0
no_password = 0
for a in db.user_accounts.find({}, {'passwordHash':1}):
    ph = a.get('passwordHash')
    if not ph:
        no_password += 1
    else:
        if isinstance(ph,str) and ph.startswith('$2'):
            bcrypt_like += 1
        else:
            plaintext_like += 1
# passwordStatus distribution
pwstatus = list(db.user_accounts.aggregate([{'$group':{'_id':'$passwordStatus','count':{'$sum':1}}}]))
mustchange = list(db.user_accounts.aggregate([{'$group':{'_id':'$mustChangePassword','count':{'$sum':1}}}]))
# createdAt earliest/latest
created_dates = [a.get('createdAt') for a in db.user_accounts.find({}, {'createdAt':1}) if a.get('createdAt')]
parsed=[]
for d in created_dates:
    if isinstance(d, datetime): parsed.append(d)
    else:
        try: parsed.append(datetime.fromisoformat(str(d)))
        except: pass
if parsed:
    earliest=min(parsed).isoformat(); latest=max(parsed).isoformat()
else:
    earliest=None; latest=None
print('ACCOUNTS_TOTAL=',accounts_count)
print('ACCOUNTS_WITH_PASSWORDHASH=',with_hash)
print('ACCOUNTS_BCRYPT_LIKE=',bcrypt_like)
print('ACCOUNTS_PLAINTEXT_LIKE=',plaintext_like)
print('ACCOUNTS_NO_PASSWORDHASH=',no_password)
print('PASSWORDSTATUS_DISTRIBUTION=')
for p in pwstatus:
    print(' -',p['_id'],p['count'])
print('MUSTCHANGEPASSWORD_DISTRIBUTION=')
for m in mustchange:
    print(' -',m['_id'],m['count'])
print('EARLIEST_CREATED_AT=',earliest)
print('LATEST_CREATED_AT=',latest)
