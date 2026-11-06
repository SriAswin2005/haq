"""Rescore saved real replies using current cases/checks, without changing raw."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.run_eval import load_cases, latest_record, digest, utc_now, write_json
from tests.reporting import analyse, write_reports, referral_metrics
from tests.round3_reports import performance


def current_records(run):
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    if manifest['mock'] or manifest['stage']!='real' or manifest['runs']!=1:
        raise ValueError('Use a single-repeat real run')
    cases={c['id']:c for c in load_cases(ROOT/'tests/cases.jsonl')}
    corpus=json.loads((run/'corpus_snapshot.json').read_text(encoding='utf-8'))
    records=[]
    for cid in manifest['case_ids']:
        raw,path=latest_record(run/'raw',cid)
        if not raw or raw.get('error'):
            raise ValueError('Missing or infrastructure-failed case '+cid)
        if any(raw['case'].get(k)!=cases[cid].get(k) for k in ['turns','mode','language','input_mode','expected_referral_any','expected_chunk_ids']):
            raise ValueError('Input/target changed for '+cid)
        records.append({'case':cases[cid],'repeat':1,'raw':raw,'path':path})
    return manifest,corpus,records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--publish',action='store_true',help='Publish a fresh-run offline rescore, preserving original scoring')
    args=parser.parse_args()
    run=args.run.resolve()
    if not run.is_relative_to((ROOT/'outputs/runs').resolve()):
        raise ValueError('Select a canonical archive')
    manifest,corpus,records=current_records(run)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    dest=run/'rescores'/('policy-v2-'+stamp)
    dest.mkdir(parents=True,exist_ok=False)
    hashes={str(r['path'].relative_to(run)):digest(r['path']) for r in records}
    summary=write_reports(dest,manifest,records,corpus,publish_bugs=False)
    items=[analyse(r,corpus) for r in records]
    rows={r['case_id']:r for r in csv.DictReader((run/'results.csv').open(encoding='utf-8'))}
    changes=[{'case_id':i['case']['id'],'before':rows[i['case']['id']]['status'],'rescored':i['status'],
        'failing_checks':[n for n,v in i['checks'].items() if v.status=='fail'],
        'domains':i['turn_checks'][-1]['check_domains'].details} for i in items]
    if any(digest(run/rel)!=sha for rel,sha in hashes.items()):
        raise ValueError('Raw bytes changed')
    payload={'rescored_at':utc_now(),'parent_run':str(run),'directory':str(dest),'additional_api_calls':0,
        'raw_sha256':hashes,'raw_hashes_unchanged':True,'original_published_passes':sum(r['status']=='pass' for r in rows.values()),
        'summary':summary,'referrals':referral_metrics(items),'performance':performance(items),
        'analysis_sha256':{n:digest(ROOT/'tests'/n) for n in ['checks.py','cases.jsonl','reporting.py']},'case_results':changes}
    for name in ['checks.py','cases.jsonl','reporting.py']:
        shutil.copyfile(ROOT/'tests'/name,dest/name)
    write_json(dest/'rescore.json',payload)
    pointer={'run':str(run),'rescore':str(dest),'raw_sha256':hashes,'analysis_sha256':payload['analysis_sha256'],'summary':summary}
    if args.publish:
        original=run/'scoring-original'
        if not original.exists():
            original.mkdir()
            for name in ['summary.md','results.csv','calibration.md','BUGS.md','completion.json']:
                shutil.copyfile(run/name,original/name)
            frozen=json.loads((run/'frozen_inputs.json').read_text(encoding='utf-8'))
            shutil.copyfile(Path(frozen['snapshot_root'])/'tests/checks.py',original/'checks.py')
        for name in ['summary.md','results.csv','calibration.md','BUGS.md']:
            shutil.copyfile(dest/name,run/name)
        for name in ['summary.md','results.csv','calibration.md']:
            shutil.copyfile(dest/name,ROOT/'outputs'/name)
        shutil.copyfile(dest/'BUGS.md',ROOT/'tests/BUGS.md')
        shutil.copyfile(dest/'BUGS.md',run/'BUGS_checks_only.md')
        done=json.loads((original/'completion.json').read_text(encoding='utf-8'))
        write_json(run/'completion.json',{**done,**summary,'offline_rescored_at':utc_now(),'additional_api_calls':0})
        write_json(run/'policy_v2_rescore.json',pointer)
    else:
        write_json(ROOT/'tests/policy_v2_baseline.json',pointer)
    text=(dest/'summary.md').read_text(encoding='utf-8')
    text='# Offline rescore of the last real run\n\nParent: '+run.name+'; zero API calls; raw files unchanged.\n\n'+text
    (dest/'summary.md').write_text(text,encoding='utf-8')
    if not args.publish:
        shutil.copyfile(dest/'summary.md',ROOT/'outputs/rescore_summary.md')
    print(json.dumps({'rescore':str(dest),'summary':summary,'referrals':payload['referrals']},sort_keys=True))


if __name__=='__main__':
    main()
