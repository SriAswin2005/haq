"""Compare a fresh real run with the last capture under corrected checks."""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.recheck_eval import current_records
from tests.reporting import analyse, referral_metrics, rate
from tests.round3_reports import summarise, performance, show, delta, failed_checks
from tests.run_eval import digest,utc_now,write_json


def verify_commit_sources(snapshot, frozen):
    paths=[rel for rel in frozen['input_sha256'] if Path(rel).parts[0]=='app' or
        Path(rel).parts[:2]==('data','corpus') or rel in [str(Path(x)) for x in ['config.yaml','data/validate_corpus.py','docs/claude_code_report.md']]]
    requests=''.join(f"{frozen['git_commit']}:{Path(rel).as_posix()}\n" for rel in paths).encode()
    data=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=requests,capture_output=True,check=True).stdout
    offset=0
    text_suffixes={'.py','.js','.css','.html','.json','.jsonl','.yaml','.md','.txt','.svg','.webmanifest'}
    for rel in paths:
        end=data.index(b'\n',offset); header=data[offset:end].split();offset=end+1
        if len(header)!=3 or header[1]!=b'blob':raise ValueError('Missing committed blob: '+rel)
        size=int(header[2]);blob=data[offset:offset+size];offset+=size+1
        actual=(snapshot/rel).read_bytes()
        if Path(rel).suffix in text_suffixes:
            blob=blob.replace(b'\r\n',b'\n');actual=actual.replace(b'\r\n',b'\n')
        if blob!=actual:raise ValueError('Snapshot differs from committed source: '+rel)
    return len(paths)


def domain_metrics(items):
    turns=[(i,n,c['check_domains']) for i in items for n,c in enumerate(i['turn_checks'],1)]
    bad=[{'case_id':i['case']['id'],'turn':n,'domains':o.details.get('ungrounded',[])} for i,n,o in turns if o.status=='fail']
    shown=sum(len(o.details.get('shown',[])) for _,_,o in turns)
    missing=sum(len(o.details.get('ungrounded',[])) for _,_,o in turns)
    return {'turns':len(turns),'passing_turns':sum(o.status=='pass' for _,_,o in turns),
        'shown_domains':shown,'grounded_domains':shown-missing,'failing_cases':len({r['case_id'] for r in bad}),'failures':bad}


def generate(run):
    if not run.is_relative_to((ROOT/'outputs/runs').resolve()):
        raise ValueError('Select a canonical archive')
    baseline=json.loads((ROOT/'tests/policy_v2_baseline.json').read_text(encoding='utf-8'))
    before=Path(baseline['run']);rescore=Path(baseline['rescore'])
    saved=json.loads((rescore/'rescore.json').read_text(encoding='utf-8'))
    for name,sha in saved['analysis_sha256'].items():
        if digest(ROOT/'tests'/name)!=sha:
            raise ValueError('Baseline scorer/expectations changed: '+name)
    bm,bc,br=current_records(before);am,ac,ar=current_records(run)
    if am['case_ids']!=[f'T-{n:03d}' for n in range(1,56)] or am['judge']:
        raise ValueError('Use all 55 cases without an extra judge')
    for name,key in [('checks.py','checks'),('cases.jsonl','cases'),('reporting.py','reporting')]:
        if digest(ROOT/'tests'/name)!=am['fingerprints'][key]:
            pointer=run/'policy_v2_rescore.json'
            if name!='checks.py' or not pointer.exists():
                raise ValueError('Current analysis differs from capture: '+name)
            fresh_rescore=json.loads(pointer.read_text(encoding='utf-8'))
            if fresh_rescore['analysis_sha256']!=saved['analysis_sha256']:
                raise ValueError('Fresh and baseline rescores use different rules')
    old=[analyse(r,bc) for r in br];new=[analyse(r,ac) for r in ar]
    if sum(i['status']=='pass' for i in old)!=saved['summary']['passed']:
        raise ValueError('Rescored baseline did not reproduce')
    for rel,sha in saved['raw_sha256'].items():
        if digest(before/rel)!=sha:
            raise ValueError('Prior raw bytes changed')
    frozen=json.loads((run/'frozen_inputs.json').read_text(encoding='utf-8'))
    snapshot=Path(frozen['snapshot_root']).resolve()
    if not snapshot.is_relative_to((ROOT/'tests/_scratch').resolve()) or not frozen.get('snapshot_from_commit'):
        raise ValueError('Use the requested committed-source snapshot')
    if any(digest(snapshot/rel)!=sha for rel,sha in frozen['input_sha256'].items()):
        raise ValueError('Frozen inputs changed')
    verified_commit_files=verify_commit_sources(snapshot,frozen)
    hashes={}
    for r in ar:
        rel=r['path'].relative_to(run);sha=digest(r['path'])
        if sha!=digest(snapshot/'outputs/runs'/run.name/rel) or sha!=digest(ROOT/'outputs/raw'/(r['case']['id']+'.json')):
            raise ValueError('Raw collection/publication mismatch')
        hashes[str(rel)]=sha
    if (run/'policy_v2_rescore.json').exists() and hashes!=json.loads((run/'policy_v2_rescore.json').read_text(encoding='utf-8'))['raw_sha256']:
        raise ValueError('Fresh rescore raw hashes differ')
    om,nm=summarise(old),summarise(new)
    op,np=performance(old),performance(new)
    of,nf=referral_metrics(old),referral_metrics(new)
    od,nd=domain_metrics(old),domain_metrics(new)
    old_rows={r['case_id']:r for r in csv.DictReader((before/'results.csv').open(encoding='utf-8'))}
    old_by={i['case']['id']:i for i in old}
    capture_done=run/'scoring-original/completion.json'
    capture_passes=json.loads((capture_done if capture_done.exists() else run/'completion.json').read_text(encoding='utf-8'))['passed']
    lines=['# Before / after — corrected checks, fresh full real eval','',
        f"Last run: `{before.name}`. Fresh run: `{run.name}`.",
        f"Fresh app/config/corpus: commit `{frozen['git_commit']}`, captured at {frozen['frozen_at']}. Parallel working-tree edits were preserved and excluded. "
        'The current corrected tests were copied separately. All T-001..T-055 ran once with six-second spacing and no extra `--judge`.', '',
        '| Scoring view | Strict case passes |','|---|---:|',
        f"| Last run as published | {saved['original_published_passes']}/55 |",
        f"| Same last-run replies, corrected checks/expectations | {saved['summary']['passed']}/55 |",
        f"| Fresh real run, same corrected checks/expectations | {nm['Case pass']['numerator']}/55 |",'',
        'The model/revision comparison below uses the rescored baseline, so test-rule changes are not presented as product improvements. '
        'Original raw files and published last-run scores are untouched. The offline rescore made zero API calls; its evidence is under `'+str(rescore.relative_to(before))+'`.','',
        'Post-capture validation corrected sentence-ending URL punctuation and two duplicate-body recognitions (IRDAI\'s qualified internal department and the Hindi District Commission label). '
        f"Both datasets use identical final checks. The fresh original scoring ({capture_passes}/55) is preserved in scoring-original/; final scoring is {nm['Case pass']['numerator']}/55. All rescoring uses unchanged replies and zero extra API calls.",'',
        '## Matched full-run metrics','',
        '| Metric | Last run rescored | Fresh run | Delta |','|---|---:|---:|---:|']
    lines += [f'| {name} | {show(value)} | {show(nm[name])} | {delta(value,nm[name])} |' for name,value in om.items()]
    lines += ['', '## Latency','', '| Measure | Last run | Fresh run |','|---|---:|---:|',
        f"| Turns | {op['turns']} | {np['turns']} |",
        f"| p50 | {op['p50_s']:.3f} s | {np['p50_s']:.3f} s |",
        f"| p95 | {op['p95_s']:.3f} s | {np['p95_s']:.3f} s |",
        f"| Mean | {op['mean_s']:.3f} s | {np['mean_s']:.3f} s |",
        f"| Max | {op['max_s']:.3f} s | {np['max_s']:.3f} s |",'',
        'All completed turn times and outliers are included. p50/p95 use linear interpolation at (n-1)*p; the six-second inter-turn sleep is excluded. '
        'Rescoring does not change timings. Provider load, models and app changes can all affect the observed difference.','',
        '## Referral precision/recall — T-041..T-055','',
        '| Measure | Last run rescored | Fresh run |','|---|---:|---:|',
        f"| Acceptable referral precision, specific bodies + permitted follow-ups / shown | {rate(of['correct_bodies'],of['shown_bodies'])} | {rate(nf['correct_bodies'],nf['shown_bodies'])} |",
        f"| Specific-body recall, cases naming expected body / expected cases | {rate(of['correct_cases'],of['expected_cases'])} | {rate(nf['correct_cases'],nf['expected_cases'])} |",
        f"| Cited-specific-body recall | {rate(of['cited_correct_cases'],of['expected_cases'])} | {rate(nf['cited_correct_cases'],nf['expected_cases'])} |",
        f"| Permitted next-step body mentions | {of['allowed_followup_bodies']} | {nf['allowed_followup_bodies']} |",
        f"| Wrong-body cases | {of['wrong_body_cases']} | {nf['wrong_body_cases']} |",
        f"| Referral check pass, fallback allowed | {rate(of['referral_check_passes'],of['expected_cases'])} | {rate(nf['referral_check_passes'],nf['expected_cases'])} |",'',
        'Bodies/destinations are deduplicated per reply. Recall still requires the expected specific body; NCH/District Commission follow-ups do not substitute for it. '
        'The exception is limited to consumer/wages answers with the specific body first and a sequential cue or an explicitly additional later paragraph. '
        'Equal first options, earlier generic bodies and escalation replies still hard fail. Answers still require a named-and-cited expected body.','',
        '## Website and email domain grounding','',
        '| Measure | Last run rescored | Fresh run |','|---|---:|---:|',
        f"| Domain-check passing turns | {od['passing_turns']}/{od['turns']} | {nd['passing_turns']}/{nd['turns']} |",
        f"| Grounded displayed domains | {rate(od['grounded_domains'],od['shown_domains'])} | {rate(nd['grounded_domains'],nd['shown_domains'])} |",
        f"| Cases with domain mismatches (hard fail) | {od['failing_cases']} | {nd['failing_cases']} |",'',
        'Every website/email hostname in reply or draft must occur in a retrieved chunk (including its source URL) or the user history available on that turn. '
        'Case/IDNA and optional www are normalized. A parent domain does not authorize an unlisted subdomain. Entire-corpus or cited-but-unretrieved evidence earns no domain credit.','']
    for label,dm in [('Last run',od),('Fresh run',nd)]:
        lines += [f"- {label}: "+('; '.join(f"{x['case_id']} turn {x['turn']}: {', '.join(x['domains'])}" for x in dm['failures']) or 'no domain mismatches')+'.']
    lines += ['', '## Per-case delta','', '| Case | Last published | Last rescored → fresh | Resolved checks | New failures |','|---|---|---|---|---|']
    for item in new:
        cid=item['case']['id'];prev=old_by[cid]
        lines.append(f"| {cid} | {old_rows[cid]['status']} | {prev['status']} → {item['status']} | {', '.join(sorted(failed_checks(prev)-failed_checks(item))) or 'none'} | {', '.join(sorted(failed_checks(item)-failed_checks(prev))) or 'none'} |")
    lines += ['', '## Fresh referral observations','', '| Case | Category / action / lawyer | Specific body | Allowed next step | Wrong body | Referral check | Domain check |','|---|---|---|---|---|---|---|']
    observations=[]
    for item in new:
        if 'expected_referral_any' not in item['case']:continue
        r=item['raw']['turns'][-1]['result'];o=item['turn_checks'][-1]['check_referral'];d=item['turn_checks'][-1]['check_domains']
        observations.append({'case_id':item['case']['id'],'check':o.status,'domains':d.details,**o.details})
        lines.append(f"| {item['case']['id']} | {r['category']} / {r['action']} / {r['needs_lawyer']} | {', '.join(o.details['correct']) or 'none'} | {', '.join(o.details['allowed_followups']) or 'none'} | {', '.join(o.details['wrong']) or 'none'} | {o.status} | {d.status} |")
    lines += ['', '## Check revisions and limits','',
        'Negated guarantees, including bullets under an explicit unverified-information heading, are not positive promises. A later affirmative promise remains a failure. '
        'PF T-044 accepts wages/answer when EPFO is named and cited; either lawyer flag is allowed, with a visible lawyer pointer required when true. '
        'All inputs, specific-body allowlists and law-verification flags are unchanged. All 55 law expectations still require human confirmation.',
        'No app/data source was edited. Domain and statute/reference checks are textual grounding checks, not a complete legal-applicability audit. '
        'The configured app verifier stayed enabled; there was no extra harness judge. Semantic unsupported-claim rate and repeated-run stability are unavailable.']
    text='\n'.join(lines)+'\n'
    for directory in [run,ROOT/'outputs']:
        (directory/'BEFORE_AFTER.md').write_text(text,encoding='utf-8')
    (run/'referrals.md').write_text('# Referral and domain results\n\n'+'\n'.join(lines[lines.index('## Referral precision/recall — T-041..T-055'):])+'\n',encoding='utf-8')
    shutil.copyfile(run/'referrals.md',ROOT/'outputs/referrals.md')
    with (run/'referrals.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(observations[0]));writer.writeheader()
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in observations)
    shutil.copyfile(run/'referrals.csv',ROOT/'outputs/referrals.csv')
    perf_text=f"# Performance — {run.name}\n\n{np['turns']} turns; p50 {np['p50_s']:.3f} s; p95 {np['p95_s']:.3f} s; mean {np['mean_s']:.3f} s.\n\n"
    perf_text+='All observed turn times included; inter-turn sleeps excluded. See BEFORE_AFTER.md for the matched baseline.\n\n| Role | Served model | Entries |\n|---|---|---:|\n'
    perf_text+='\n'.join(f"| {m['role']} | {m['model']} | {m['entries']} |" for m in np['served_role_models'])+'\n'
    for directory in [run,ROOT/'outputs']:(directory/'perf.md').write_text(perf_text,encoding='utf-8')
    base=run/'BUGS_checks_only.md'
    if not base.exists():base.write_bytes((run/'BUGS.md').read_bytes())
    context=f"# Evaluation bugs\n\nFresh complete real run from commit {frozen['git_commit']}, frozen {frozen['frozen_at']}. Corrected guarantee/PF/secondary-referral/domain rules apply. Historical captures are preserved.\n"
    bugs=base.read_text(encoding='utf-8').replace('# Evaluation bugs\n',context,1)
    bugs='\n'.join(line.rstrip() for line in bugs.splitlines()).rstrip()+'\n'
    for path in [run/'BUGS.md',ROOT/'tests/BUGS.md']:path.write_text(bugs,encoding='utf-8')
    payload={'generated_at':utc_now(),'before_run':str(before),'baseline_rescore':str(rescore),'after_run':str(run),
        'original_published_passes':saved['original_published_passes'],'before_rescored':om,'after':nm,
        'referrals_before':of,'referrals_after':nf,'referral_observations':observations,'domains_before':od,'domains_after':nd,'performance_before':op,'performance_after':np,
        'raw_sha256':hashes,'before_raw_sha256':saved['raw_sha256'],'git_commit':frozen['git_commit'],
        'snapshot_from_commit':True,'frozen_inputs_unchanged':True,'raw_byte_identity':True,'additional_api_calls':0}
    write_json(run/'policy_v2_metrics.json',payload)
    from dotenv import dotenv_values
    values=[*dotenv_values(ROOT/'.env',encoding='utf-8-sig').items(),*os.environ.items()]
    secrets=[v.encode() for k,v in values if v and len(v)>=8 and any(w in k.upper() for w in ['KEY','TOKEN','SECRET','PASSWORD'])]
    files=[p for p in run.rglob('*') if p.is_file()]
    if (snapshot/'.env').exists() or any(v in p.read_bytes() for p in files for v in secrets):raise ValueError('Credential exposure detected; values withheld')
    write_json(run/'audit.json',{'audited_at':utc_now(),'raw_cases':55,'turns':np['turns'],'raw_hashes_unchanged':True,
        'baseline_raw_hashes_preserved':True,'frozen_inputs_unchanged':True,'app_config_corpus_from_commit':frozen['git_commit'],
        'committed_source_files_verified':verified_commit_files,'text_line_endings_normalized_for_commit_comparison':True,
        'credential_value_matches':0,'additional_api_calls':0})
    print(json.dumps({'before_rescored_passes':om['Case pass']['numerator'],'new_passes':nm['Case pass']['numerator'],
        'referrals':nf,'domains':nd,'p50_s':np['p50_s'],'p95_s':np['p95_s']},sort_keys=True))
    return payload


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    generate(args.run.resolve())


if __name__=='__main__':main()
