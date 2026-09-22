#!/usr/bin/env python3
"""Offline, deterministic feasibility audit; does not run an RQ3 experiment."""
import hashlib
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = '230cf22b56a481dd1a994b21e4d94c59e2bccea9'
SOURCE = ROOT / 'data/rq3/source/vcdb'
ARCHIVE = SOURCE / f'{COMMIT}.tar.gz'
OUT = ROOT / 'data/rq3/vcdb_audit_v1'
CYBER = ('hacking', 'malware', 'social')
UNKNOWN = {'unknown', 'other', 'na', 'n/a', 'none', '', 's - unknown',
           'u - unknown', 's - other', 'u - other'}


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def known_list(values):
    # Mixed known/unknown lists are deliberately not accepted as complete answers.
    if not isinstance(values, list) or not values:
        return []
    if any(not isinstance(v, str) or v.strip().lower() in UNKNOWN or
           v.strip().lower().endswith(' - unknown') or
           v.strip().lower().endswith(' - other') for v in values):
        return []
    return sorted(set(v.strip() for v in values))


def norm(value):
    return ' '.join(str(value or '').lower().split())


def ids(row):
    return {norm(row.get('incident_id')), norm(row.get('plus', {}).get('master_id'))} - {''}


def fields(row):
    result = {}
    for category in CYBER:
        for key in ('variety', 'vector'):
            values = known_list(row.get('action', {}).get(category, {}).get(key))
            if values:
                result[f'action.{category}.{key}'] = values
    for path, objects in [
        ('asset.assets[].variety', row.get('asset', {}).get('assets', [])),
        ('attribute.confidentiality.data[].variety',
         row.get('attribute', {}).get('confidentiality', {}).get('data', [])),
    ]:
        values = known_list([o.get('variety') for o in objects])
        if values:
            result[path] = values
    return result


def families(available):
    return {('technique' if p.endswith('.variety') else 'vector')
            if p.startswith('action.') else ('asset' if p.startswith('asset.') else 'data')
            for p in available}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, buckets = [], Counter()
    with tarfile.open(ARCHIVE) as archive:
        for member in archive:
            rel = member.name.split('/', 1)[-1]
            if rel in ('LICENSE.txt', 'data/json/README'):
                dest = SOURCE / ('LICENSE.txt' if rel == 'LICENSE.txt' else 'upstream_data_README.txt')
                dest.write_bytes(archive.extractfile(member).read())
            if rel.startswith('data/json/') and rel.endswith('.json'):
                bucket = rel.split('/')[2]
                buckets[bucket] += 1
                if bucket == 'validated':
                    rows.append((rel, json.load(archive.extractfile(member))))
    rows.sort(key=lambda item: item[0])
    identity_counts = Counter(token for _, row in rows for token in ids(row))
    stage_counts = Counter()
    exclusions, candidates = [], []
    for path, row in rows:
        available = fields(row)
        checks = [
            ('cyber_action', any(c in row.get('action', {}) for c in CYBER)),
            ('confirmed_eligible', row.get('security_incident') == 'Confirmed' and
             row.get('plus', {}).get('analysis_status') != 'Ineligible'),
            ('unambiguous_id', bool(row.get('incident_id')) and
             all(identity_counts[token] == 1 for token in ids(row))),
            ('source_url_present', bool(re.search(r'https?://\S+', row.get('reference') or ''))),
            ('three_technical_families', len(families(available)) >= 3),
        ]
        for name, ok in checks:
            if not ok:
                exclusions.append({'source_path': path, 'incident_id': row.get('incident_id'),
                                   'first_exclusion_reason': name})
                break
            stage_counts[name] += 1
        else:
            candidates.append({
                'incident_id': row['incident_id'], 'source_path': path,
                'normalized_record_sha256': hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest(),
                'answerable_fields': available,
                'technical_families': sorted(families(available)),
                'original_record': row,
            })
    for name, records in [('candidates.jsonl', candidates), ('exclusions.jsonl', exclusions)]:
        with (OUT / name).open('w') as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + '\n')
    summary_counts = Counter(norm(c['original_record'].get('summary')) for c in candidates)
    duplicate_summaries = [
        {'normalized_summary': summary, 'records': count,
         'incident_ids': [c['incident_id'] for c in candidates
                          if norm(c['original_record'].get('summary')) == summary]}
        for summary, count in summary_counts.most_common() if summary and count > 1
    ]
    write_json(OUT / 'shared_summaries.json', duplicate_summaries)
    report = {
        'status': 'feasibility_audit_not_approved_experiment',
        'source_commit': COMMIT, 'source_buckets': dict(buckets),
        'validated_records': len(rows),
        'validated_distinct_incident_ids_case_insensitive': len({norm(r.get('incident_id')) for _, r in rows}),
        'cumulative_selection_counts': dict(stage_counts),
        'candidate_records': len(candidates),
        'distinct_answerable_field_profiles': len({json.dumps(c['answerable_fields'], sort_keys=True) for c in candidates}),
        'candidate_field_counts': dict(Counter(p for c in candidates for p in c['answerable_fields'])),
        'candidate_year_counts': dict(sorted(Counter(str(c['original_record'].get('timeline', {}).get('incident', {}).get('year')) for c in candidates).items())),
        'candidate_action_counts_overlapping': dict(Counter(k for c in candidates for k in CYBER if k in c['original_record'].get('action', {}))),
        'candidate_analysis_status_counts': dict(Counter(str(c['original_record'].get('plus', {}).get('analysis_status')) for c in candidates)),
        'candidate_shared_summary_groups': len(duplicate_summaries),
        'candidate_records_in_shared_summary_groups': sum(g['records'] for g in duplicate_summaries),
        'largest_shared_summary_groups': [{k: v for k, v in g.items() if k != 'incident_ids'} for g in duplicate_summaries[:5]],
        'limits': [
            'validated is the upstream structural validation label, not independent factual verification',
            'references are present but their availability and factual support have not been verified',
            'unique identifiers do not establish independent incidents; shared campaigns require grouping',
            'three technical families is a proposed feasibility threshold, not an approved protocol',
            'known labels are preserved verbatim; English taxonomy remains untranslated',
            'candidate fields support answers according to the record, not exhaustive claims about the incident',
        ],
    }
    write_json(OUT / 'audit.json', report)
    examples = []
    prompts = {
        'asset.assets[].variety': 'Quali tipi di risorse coinvolte sono registrati nella scheda del caso {id}?',
        'attribute.confidentiality.data[].variety': 'Quali categorie di dati sono registrate nella scheda del caso {id}?',
    }
    # Illustration only: one single-summary candidate per main action category.
    for category in CYBER:
        candidate = next((c for c in candidates if any(p.startswith(f'action.{category}.') for p in c['answerable_fields'])
                          and summary_counts[norm(c['original_record'].get('summary'))] == 1), None)
        if candidate is None:
            continue
        for path, answer in candidate['answerable_fields'].items():
            prompt = prompts.get(path)
            if prompt is None:
                key = 'tipologie sono registrate' if path.endswith('.variety') else 'vettori sono registrati'
                prompt = f'Quali {key} sotto {path.split(".")[1]} nella scheda del caso {{id}}?'
            examples.append({'status': 'illustrative_not_evaluation', 'incident_id': candidate['incident_id'],
                             'source_path': candidate['source_path'], 'evidence_field': path,
                             'question': prompt.format(id=candidate['incident_id']), 'expected_record_values': answer})
    write_json(OUT / 'question_examples.json', examples)
    write_json(SOURCE / 'manifest.json', {
        'repository': 'https://github.com/vz-risk/VCDB', 'commit': COMMIT,
        'commit_date': '2026-08-04T00:05:58Z',
        'download_url': f'https://codeload.github.com/vz-risk/VCDB/tar.gz/{COMMIT}',
        'archive_filename': ARCHIVE.name, 'archive_bytes': ARCHIVE.stat().st_size,
        'archive_sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        'license_as_declared_upstream': 'CC-BY-SA-4.0',
        'attribution': 'VERIS Community Database (VCDB), vz-risk contributors',
        'audit_script': 'scripts/rq3/audit_vcdb.py',
        'transformations': 'Original archive retained; selected records copied unchanged inside candidates.jsonl; field projections and audit metadata added.',
    })
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
