#!/usr/bin/env python3
"""Acquisizione e congelamento della sorgente di RQ3 / SC07.

Scarica dal GitHub Advisory Database soltanto il sottoalbero
`advisories/github-reviewed` e `LICENSE.md` **al commit dichiarato nella
configurazione** (fetch del commit esatto, sparse checkout, nessun checkout
di HEAD). Con quei file costruisce uno snapshot tar.gz deterministico e
scrive il manifest con:

  - URL del repository, commit, data del commit e hash dell'albero git del
    sottoalbero usato;
  - data di acquisizione;
  - SHA-256, dimensione e numero di file dello snapshot;
  - SHA-256 dell'elenco ordinato `percorso<TAB>sha256` di tutti i file;
  - licenza: identificativo SPDX, file conservato e suo SHA-256.

Non seleziona nessun record. Con `--verify` non usa la rete: controlla che
snapshot, licenza, manifest e configurazione coincidano.

Uso (dalla radice del progetto):
    python3 scripts/rq3/acquire_rq3_sc07_source.py            # acquisizione
    python3 scripts/rq3/acquire_rq3_sc07_source.py --verify   # solo verifica

Dopo la prima acquisizione lo SHA-256 dello snapshot va registrato in
`source.snapshot_sha256` della configurazione (lo script lo stampa e, con
`--write-config-hash`, lo scrive se il campo e' ancora vuoto).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402


def git(args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, check=True,
                            capture_output=True, text=True)
    return result.stdout.strip()


def fetch_sparse(repository_url, commit, subtree, license_name, workdir):
    """Checkout sparso del commit esatto. Ritorna i metadati git."""
    git(["init", "-q"], workdir)
    git(["remote", "add", "origin", repository_url], workdir)
    git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit], workdir)
    git(["sparse-checkout", "set", "--no-cone", f"/{subtree.strip('/')}/", f"/{license_name}"], workdir)
    git(["checkout", "-q", "FETCH_HEAD"], workdir)
    head = git(["rev-parse", "HEAD"], workdir)
    if head != commit:
        raise RuntimeError(f"HEAD {head} diverso dal commit dichiarato {commit}")
    return {
        "commit_date": git(["show", "-s", "--format=%cI", commit], workdir),
        "commit_subject": git(["show", "-s", "--format=%s", commit], workdir),
        "subtree_git_tree": git(["rev-parse", f"{commit}:{subtree.strip('/')}"], workdir),
        "license_git_blob": git(["rev-parse", f"{commit}:{license_name}"], workdir),
    }


def collect_files(workdir, subtree, license_name):
    root = Path(workdir)
    entries = []
    for path in sorted((root / subtree).rglob("*")):
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(), path.read_bytes()))
    entries.append((license_name, (root / license_name).read_bytes()))
    return entries


def file_listing_sha256(entries):
    lines = "".join(f"{p}\t{common.sha256_bytes(d)}\n" for p, d in sorted(entries))
    return common.sha256_text(lines)


def acquire(config, repo_root=common.REPO_ROOT, workdir=None):
    source = config["source"]
    commit = source["commit"]
    license_name = source["license_file_in_repository"]
    with tempfile.TemporaryDirectory(prefix="rq3_sc07_ghsa_") as tmp:
        work = Path(workdir or tmp)
        work.mkdir(parents=True, exist_ok=True)
        git_meta = fetch_sparse(source["repository_url"], commit, source["subtree"], license_name, work)
        entries = collect_files(work, source["subtree"], license_name)

    out_dir = common.source_dir(config, repo_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot = common.snapshot_path(config, repo_root)
    snapshot_sha = common.build_deterministic_tar_gz(entries, f"advisory-database-{commit}", snapshot)

    license_bytes = dict(entries)[license_name]
    license_path = out_dir / license_name
    license_path.write_bytes(license_bytes)

    advisory_files = [p for p, _ in entries if p.endswith(".json")]
    manifest = {
        "dataset": source["dataset"],
        "citation": source["citation"],
        "repository_url": source["repository_url"],
        "commit": commit,
        "commit_date": git_meta["commit_date"],
        "commit_subject": git_meta["commit_subject"],
        "acquired_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acquisition_method": (
            "git fetch --depth 1 --filter=blob:none <commit>; sparse checkout of "
            f"/{source['subtree']}/ and /{license_name}; deterministic tar.gz "
            "(sorted members, mtime 0, uid/gid 0, mode 0644, gzip mtime 0)"
        ),
        "subtree": source["subtree"],
        "subtree_git_tree": git_meta["subtree_git_tree"],
        "snapshot": {
            "path": common.rel(snapshot, repo_root),
            "sha256": snapshot_sha,
            "bytes": snapshot.stat().st_size,
            "root_in_archive": f"advisory-database-{commit}",
            "advisory_json_files": len(advisory_files),
            "total_files": len(entries),
            "file_listing_sha256": file_listing_sha256(entries),
        },
        "license": {
            "spdx": source["license_spdx"],
            "filename": license_name,
            "path": common.rel(license_path, repo_root),
            "sha256": common.sha256_bytes(license_bytes),
            "git_blob": git_meta["license_git_blob"],
            "first_line": license_bytes.decode("utf-8").splitlines()[0].strip(),
        },
        "indirect_provenance": source["indirect_provenance"],
        "transformations": (
            "Nessuna modifica ai file upstream: lo snapshot contiene i JSON OSV originali "
            "del sottoalbero e la licenza. I record selezionati sono proiettati nei "
            "campi usati, con percorso e SHA-256 del file originale."
        ),
        "script": "scripts/rq3/acquire_rq3_sc07_source.py",
    }
    common.dump_json(common.manifest_path(config, repo_root), manifest)
    return manifest


def write_config_hash(snapshot_sha, config_path=common.CONFIG_PATH):
    """Registra lo SHA-256 nella configurazione solo se il campo e' vuoto."""
    text = Path(config_path).read_text(encoding="utf-8")
    config = json.loads(text)
    current = config["source"].get("snapshot_sha256")
    if current == snapshot_sha:
        return False
    if current:
        raise ValueError(f"la configurazione registra gia' un hash diverso: {current}")
    needle = '"snapshot_sha256": null'
    if text.count(needle) != 1:
        raise ValueError("campo snapshot_sha256 non trovato una sola volta")
    Path(config_path).write_text(text.replace(needle, f'"snapshot_sha256": "{snapshot_sha}"'), encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="solo verifica offline")
    parser.add_argument("--write-config-hash", action="store_true",
                        help="registra lo SHA-256 dello snapshot nella configurazione se vuoto")
    args = parser.parse_args(argv)
    config = common.load_config()

    if args.verify:
        manifest = common.verify_snapshot(config)
        print("Snapshot verificato.")
        print(f"  commit:   {manifest['commit']} ({manifest['commit_date']})")
        print(f"  sha256:   {manifest['snapshot']['sha256']}")
        print(f"  file:     {manifest['snapshot']['advisory_json_files']} advisory JSON")
        print(f"  licenza:  {manifest['license']['spdx']} ({manifest['license']['sha256'][:16]}...)")
        return 0

    manifest = acquire(config)
    snapshot = manifest["snapshot"]
    print(f"Commit {manifest['commit']} del {manifest['commit_date']}")
    print(f"Snapshot: {snapshot['path']} ({snapshot['bytes']} byte, {snapshot['advisory_json_files']} advisory)")
    print(f"SHA-256:  {snapshot['sha256']}")
    if args.write_config_hash:
        changed = write_config_hash(snapshot["sha256"])
        print("Hash registrato nella configurazione." if changed else "Hash gia' registrato.")
    elif config["source"].get("snapshot_sha256") != snapshot["sha256"]:
        print("ATTENZIONE: source.snapshot_sha256 della configurazione non coincide; "
              "nessuna selezione e' possibile finche' non viene registrato.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
