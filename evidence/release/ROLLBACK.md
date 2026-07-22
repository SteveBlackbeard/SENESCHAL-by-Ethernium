# Rollback

1. Do not modify or delete the preserved source checkout.
2. To undo the personal line locally, remove only this isolated clone or reset it to a known private commit.
3. To undo a remote publication, disable access or archive the private repository before deletion.
4. Restore from the source repository at commit $SourceCommit; when the provenance flag says the snapshot included uncommitted work, use the preserved source checkout as the authoritative recovery input.
5. Verify restored files against MANIFEST.json or CHECKSUMS.sha256 before use.

No rollback step writes into the source checkout automatically.
