import csv
import hashlib
import io
import math
from datetime import datetime, timezone

MAX_ROWS = 5000
REQUIRED_COLUMNS = ('site_id', 'label', 'latitude', 'longitude', 'weight', 'surveyed_at')
QUARANTINE_REASONS = (
 'missing_columns', 'invalid_coordinate', 'invalid_weight', 'invalid_surveyed_at',
 'empty_site_id', 'empty_label', 'duplicate_in_batch', 'dataset_capacity_exceeded',
)

def parse_surveyed_at(raw):
 if raw is None:raise ValueError('missing')
 text=str(raw).strip()
 if not text:raise ValueError('missing')
 normalized=text.replace('Z','+00:00')
 dt=datetime.fromisoformat(normalized)
 if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
 return dt.astimezone(timezone.utc).isoformat()

def parse_csv(csv_text):
 reader=csv.DictReader(io.StringIO(csv_text.lstrip('﻿')))
 fields=reader.fieldnames or []
 missing=[name for name in REQUIRED_COLUMNS if name not in fields]
 if missing:raise ValueError('CSV需要site_id,label,latitude,longitude,weight,surveyed_at列，缺少：'+','.join(missing))
 accepted,quarantined,seen=[],[],set()
 for line_number,raw in enumerate(reader,2):
  reason=None;parsed=None
  site_id=(raw.get('site_id') or '').strip();label=(raw.get('label') or '').strip()
  try:surveyed_at=parse_surveyed_at(raw.get('surveyed_at'))
  except (ValueError,TypeError):reason='invalid_surveyed_at'
  if reason is None and not site_id:reason='empty_site_id'
  if reason is None and not label:reason='empty_label'
  if reason is None:
   try:
    lat=float(raw['latitude']);lon=float(raw['longitude'])
    if not (-90<=lat<=90 and -180<=lon<=180) or not (lat==lat and lon==lon):raise ValueError()
   except (ValueError,TypeError):reason='invalid_coordinate'
  if reason is None:
   try:
    weight=float(raw['weight'])
    if not math.isfinite(weight) or weight<0:raise ValueError()
   except (ValueError,TypeError):reason='invalid_weight'
  if reason is None and site_id in seen:reason='duplicate_in_batch'
  if reason is None:
   parsed={'site_id':site_id,'label':label,'latitude':lat,'longitude':lon,'weight':weight,'surveyed_at':surveyed_at}
  if reason:
   quarantined.append({'line_number':line_number,'site_id':site_id,'reason':reason,'raw':_safe_raw(raw,fields)})
  else:
   seen.add(site_id);accepted.append(parsed)
 return accepted,quarantined

def _safe_raw(raw,fields):
 return {k:('' if raw.get(k) is None else str(raw.get(k))) for k in fields}

def fingerprint(csv_text):
 digest=hashlib.sha256()
 digest.update(csv_text.lstrip('﻿').replace('\r\n','\n').encode('utf-8'))
 return digest.hexdigest()

def _legacy_time(row):
 return row.get('surveyed_at') or '0001-01-01T00:00:00+00:00'

def merge_rows(existing_rows,incoming):
 index={row['site_id']:i for i,row in enumerate(existing_rows)}
 inserted,updated,ignored=[],[],[]
 merged=[dict(row) for row in existing_rows]
 for row in incoming:
  site_id=row['site_id'];current=index.get(site_id)
  if current is None:
   if len(merged)>=MAX_ROWS:
    ignored.append({'site_id':site_id,'reason':'dataset_capacity_exceeded'});continue
   index[site_id]=len(merged);merged.append(dict(row));inserted.append(site_id)
  else:
   if row['surveyed_at']>_legacy_time(merged[current]):
    merged[current]=dict(row);updated.append(site_id)
   else:
    ignored.append({'site_id':site_id,'reason':'surveyed_at_not_newer'})
 return merged,{'inserted':inserted,'updated':updated,'ignored':ignored}

def summarize_batch(accepted,quarantined,merge):
 return {
  'accepted_rows':len(accepted),'quarantined_rows':len(quarantined),
  'inserted_count':len(merge['inserted']),'updated_count':len(merge['updated']),'ignored_count':len(merge['ignored']),
 }

def replay_payload(quarantined):
 out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(REQUIRED_COLUMNS))
 writer.writeheader()
 for item in quarantined:
  raw=item.get('raw') or {}
  writer.writerow({k:raw.get(k,'') for k in REQUIRED_COLUMNS})
 return out.getvalue()
