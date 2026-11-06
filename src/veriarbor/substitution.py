"""Exact certificate substitution over dependency artifacts, not old receipts."""
from dataclasses import dataclass
from .certificate import can_substitute


@dataclass(frozen=True)
class CertifiedReplacement:
    old_certificate: object
    candidate: object
    new_certificate: object
    evidence_authenticated: bool

    def permits(self, artifact, old_hash, new_hash, checkers):
        return (dict(self.old_certificate.artifact_hashes).get(artifact) == old_hash
                and dict(self.new_certificate.artifact_hashes).get(artifact) == new_hash
                and can_substitute(self.old_certificate, self.candidate,
                    replacement_certificate=self.new_certificate, checkers=checkers,
                    evidence_authenticated=self.evidence_authenticated))


def substitution_cover(previous, current, *, dependency_artifacts, replacements, checkers):
    """Return proof refs covering every delta, or None. Own artifacts never carry.

    No transitive search: only direct certified replacements passed by the host.
    A caller may not substitute checker/acceptance/schema changes with this API.
    """
    if previous.keys() != current.keys() or not all(current.values()):
        return None
    changed = {k for k in previous if previous[k] != current[k]}
    if not changed or not changed <= set(dependency_artifacts):
        return None
    proofs = {}
    for artifact in sorted(changed):
        proof = next((p for p in replacements if p.permits(artifact, previous[artifact], current[artifact], checkers)), None)
        if proof is None:
            return None
        proofs[artifact] = {'old_certificate': proof.old_certificate.fingerprint,
                            'new_certificate': proof.new_certificate.fingerprint,
                            'old_hash': previous[artifact], 'new_hash': current[artifact],
                            'evidence_refs': proof.new_certificate.evidence_refs}
    return proofs
