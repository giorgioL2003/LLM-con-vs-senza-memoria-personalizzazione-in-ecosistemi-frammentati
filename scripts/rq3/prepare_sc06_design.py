#!/usr/bin/env python3
"""Prepare a proposed SC06 dataset offline. No model calls or RQ2 integration."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/rq3/vcdb_audit_v1/candidates.jsonl'
OUT = ROOT / 'data/rq3/sc06_design_v1'
SEED = 'SC06-design-v1'
FAMILIES = ('variety', 'vector', 'asset', 'data')
LABELS = {
    'action.hacking.variety': 'Tipologie di hacking',
    'action.hacking.vector': 'Vettori di hacking',
    'action.malware.variety': 'Tipologie di malware',
    'action.malware.vector': 'Vettori di malware',
    'action.social.variety': 'Tipologie di ingegneria sociale',
    'action.social.vector': 'Vettori di ingegneria sociale',
    'asset.assets[].variety': 'Tipi di risorse coinvolte',
    'attribute.confidentiality.data[].variety': 'Categorie di dati',
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def family(path):
    if path.startswith('action.'):
        return path.split('.')[-1]
    return 'asset' if path.startswith('asset.') else 'data'


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def jsonl(name, rows):
    with (OUT / name).open('w') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with SOURCE.open() as handle:
        candidates = [json.loads(line) for line in handle]
    candidates.sort(key=lambda row: digest(SEED + ':' + row['incident_id']))
    profiles, summaries = set(), set()
    selected, decisions = [], []
    for row in candidates:
        profile = json.dumps(row['answerable_fields'], sort_keys=True)
        summary = ' '.join(row['original_record'].get('summary', '').lower().split())
        reason = ('repeated_technical_profile' if profile in profiles else
                  'repeated_nonempty_summary' if summary and summary in summaries else 'selected')
        decisions.append({'incident_id': row['incident_id'], 'decision': reason})
        if reason != 'selected':
            continue
        selected.append(row)
        profiles.add(profile)
        if summary:
            summaries.add(summary)
    # Avoid silently dropping a partial block for a future input version.
    if len(selected) % 3:
        raise ValueError('Selection is not divisible by three: revise the proposed grouping explicitly.')
    mapping, episodes, questions = [], [], []
    for start in range(0, len(selected), 3):
        block = selected[start:start + 3]
        episode_id = f'SC06-E{start // 3 + 1:03d}'
        aliases = {r['incident_id']: f'Caso {letter}' for letter, r in zip('ABC', block)}
        sessions = []
        for session_index in range(3):
            messages = []
            # Rotate order to distribute terminal positions over the three cases.
            for offset in range(3):
                row = block[(session_index + offset) % 3]
                subset = {p: v for p, v in row['answerable_fields'].items()
                          if (0 if family(p) == 'variety' else 1 if family(p) == 'vector' else 2) == session_index}
                if not subset:
                    continue
                alias = aliases[row['incident_id']]
                content = alias + '. Dati registrati nella scheda:\n' + '\n'.join(
                    f'- {LABELS[p]}: ' + '; '.join(v) for p, v in sorted(subset.items()))
                messages.append({'message_id': f'{episode_id}-S{session_index + 1}-M{len(messages) + 1}',
                                 'role': 'user', 'case_alias': alias, 'content': content})
            sessions.append({'session_id': f'{episode_id}-S{session_index + 1}', 'messages': messages})
        for row in block:
            alias = aliases[row['incident_id']]
            mapping.append({'episode_id': episode_id, 'case_alias': alias,
                            'incident_id': row['incident_id'], 'source_path': row['source_path'],
                            'reference': row['original_record'].get('reference'),
                            'answerable_fields': row['answerable_fields']})
            # Choose three distinct families; rotate the omitted one when all four exist.
            available = [f for f in FAMILIES if any(family(p) == f for p in row['answerable_fields'])]
            shift = int(digest(SEED + ':questions:' + row['incident_id'])[:8], 16) % len(available)
            chosen = (available[shift:] + available[:shift])[:3]
            for number, fam in enumerate(chosen, 1):
                fields = sorted(p for p in row['answerable_fields'] if family(p) == fam)
                path = fields[int(digest(SEED + ':field:' + row['incident_id'] + ':' + fam)[:8], 16) % len(fields)]
                question_id = f'{episode_id}-{alias[-1]}-Q{number}'
                evidence = next(m['message_id'] for s in sessions for m in s['messages']
                                if m['case_alias'] == alias and f'- {LABELS[path]}:' in m['content'])
                answer = row['answerable_fields'][path]
                other_values = {aliases[other['incident_id']]: other['answerable_fields'].get(path, [])
                                for other in block if other['incident_id'] != row['incident_id']}
                intrusion_values = sorted({v for values in other_values.values() for v in values} - set(answer))
                question = (f'Per {alias}, quali valori erano stati riportati nel campo «{LABELS[path]}»? '
                            'Riporta tutte e sole le etichette fornite, senza tradurle. '
                            'Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni '
                            'sufficienti, rispondi con {"values": []}.')
                questions.append({'question_id': question_id, 'episode_id': episode_id,
                                  'case_alias': alias, 'incident_id': row['incident_id'],
                                  'field': path, 'family': fam, 'question': question,
                                  'expected_values': answer, 'evidence_message_id': evidence,
                                  'other_cases_values_same_field': other_values,
                                  'detectable_cross_case_intrusion_values': intrusion_values})
        episodes.append({'episode_id': episode_id, 'status': 'proposed_not_executed',
                         'task_instruction': 'Memorizza le informazioni fornite sui tre casi di cybersecurity. '
                         'I nomi Caso A, Caso B e Caso C identificano casi distinti. '
                         'Le etichette tecniche provengono da VERIS: preservale come sono scritte.',
                         'sessions': sessions})
    jsonl('selection_decisions.jsonl', decisions)
    jsonl('case_mapping.jsonl', mapping)
    jsonl('episodes.jsonl', episodes)
    jsonl('queries.jsonl', [{k: q[k] for k in ('question_id', 'episode_id', 'question')} for q in questions])
    jsonl('oracle_questions.jsonl', questions)
    dump('manifest.json', {
        'status': 'proposed_not_executed', 'selection_seed': SEED,
        'input_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'candidate_records': len(candidates), 'selection_decisions': dict(Counter(d['decision'] for d in decisions)),
        'selected_cases': len(selected), 'episodes': len(episodes), 'cases_per_episode': 3,
        'ingestion_sessions_per_episode': 3, 'questions_per_case': 3, 'total_questions_per_condition': len(questions),
        'questions_with_detectable_cross_case_intrusion_values': sum(bool(q['detectable_cross_case_intrusion_values']) for q in questions),
        'question_family_counts': dict(Counter(q['family'] for q in questions)),
        'model_calls_made': 0,
        'provenance': 'VCDB commit 230cf22b56a481dd1a994b21e4d94c59e2bccea9; CC BY-SA 4.0; vz-risk contributors',
        'limitations': ['selection is not representative and does not establish incident independence',
                       'unique technical profiles deliberately reduce repeated content',
                       'shared summaries are a repetition heuristic, not verified campaign identifiers',
                       'dataset contains historical field annotations that require human spot checks',
                       'this tests case separation during one kind of activity, not multiple different cybersecurity tasks'],
    })
    example = episodes[0]
    text = ['# SC06 — esempio del formato proposto', '',
            'Fatti derivati da VERIS; messaggi costruiti automaticamente. Nessuna risposta del modello è stata generata.', '',
            f'## {example["episode_id"]}', '', example['task_instruction'], '']
    for session in example['sessions']:
        text += [f'### {session["session_id"]}', '']
        for message in session['messages']:
            text += [message['content'], '']
    text += ['### Sessione successiva: domande', '',
             'Ogni domanda parte dalla stessa memoria finale, in una conversazione nuova. '
             'Le risposte attese qui sotto sono solo per la valutazione e non vanno mostrate al modello.', '']
    for q in questions[:9]:
        text += [f'- **{q["question_id"]}:** {q["question"]}',
                 '  - Atteso: ' + ', '.join(q['expected_values']),
                 '  - Evidenza: ' + q['evidence_message_id'], '']
    text += ['## Provenienza dei tre casi', '']
    for row in mapping[:3]:
        text += [f'- {row["case_alias"]}: `{row["incident_id"]}`, `{row["source_path"]}`.',
                 f'  - Riferimento registrato in VERIS: {row["reference"]}', '']
    (OUT / 'ESEMPIO.md').write_text('\n'.join(text))
    print((OUT / 'manifest.json').read_text())


if __name__ == '__main__':
    main()
