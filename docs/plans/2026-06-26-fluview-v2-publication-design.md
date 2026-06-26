# FluView V2 Publication Design

Status: Completed

## Goal

Publish the completed FluView v2 dataset through an explicit command without
changing the behavior of `python3 flushot.py` or the legacy CSV/JSON schema.

## User Interface

The new interface is:

```text
python3 flushot.py v2 [--json-path PATH]
```

`PATH` defaults to `flu-v2.json`. With no arguments, the module continues to
call the historical `run()` path exactly as before. V2 is JSON-only because its
nested laboratory catalogs, regional records, and separate mortality grains do
not have one truthful flat CSV representation.

A subcommand is preferred over a schema flag because it makes the publication
mode explicit, leaves the default invocation untouched, gives future versioned
commands a stable namespace, and avoids implying that the legacy CSV writer can
serialize v2 records.

## Runtime Flow

`run_fluview_v2()` performs the reviewed source sequence:

1. fetch and decode phase 2 metadata;
2. fetch and decode phase 2 regional data;
3. fetch and decode ILINet CSV for HHS regions 1 through 10;
4. fetch and decode phase 4 mortality;
5. call `build_fluview_v2_dataset()`;
6. atomically publish the resulting JSON object.

The source-specific transports and decoders retain their existing URL, method,
media-type, size, UTF-8, identifier, and schema boundaries.

## Publication Safety

The v2 writer accepts only a dictionary with `schema_version == 2`. It requires
an existing parent directory and rejects an existing non-regular target. It
serializes to an invocation-owned stage in the destination directory, uses
strict finite JSON, flushes and fsyncs the complete stage, preserves an existing
file's mode, and atomically replaces the destination. Any pre-replacement
failure leaves the prior destination unchanged and removes the stage.

A single-file atomic replace does not need the paired-output backup/rollback
protocol: before replacement the old file remains authoritative; after a
successful replacement the complete fsynced v2 file is authoritative.

## Failure Policy

Every source, join, serialization, path, and publication error fails the
command. The command never falls back to stale legacy data, partial source
coverage, or a partially written v2 file.

## Testing

Tests preserve no-argument legacy dispatch, verify explicit v2 argument parsing,
mock the complete ten-region source sequence, assert the output object, exercise
invalid paths and datasets, and inject staging failures to prove the existing
file and filesystem remain clean.

## Result

Implemented the explicit `v2` command and atomic JSON writer. A live CLI run
published 380 regional records, 38 national mortality weeks, ten HHS season
totals, and the verified 184-death total without changing legacy dispatch.
