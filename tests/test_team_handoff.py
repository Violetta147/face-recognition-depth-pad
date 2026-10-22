import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from build_team_handoff import Export, excluded, restore_source_manifest
from verify_team_handoff import verify


def test_export_preserves_source_refuses_overwrite_and_detects_changed_bytes(tmp_path):
    source=tmp_path/'model.ckpt'; source.write_bytes(b'checkpoint')
    out=tmp_path/'delivery'; ex=Export(out)
    ex.copy(source,'evidence/model.ckpt','model')
    ex.finish('source',[])
    assert verify(out)['files']==1
    assert source.read_bytes()==b'checkpoint'
    with pytest.raises(FileExistsError): Export(out)
    (out/'evidence/model.ckpt').write_bytes(b'changed!!!')
    with pytest.raises(ValueError,match='changed delivery'): verify(out)


def test_export_refuses_traversal_and_hook_payloads(tmp_path):
    source=tmp_path/'s';source.write_bytes(b's')
    ex=Export(tmp_path/'delivery')
    with pytest.raises(ValueError,match='unsafe'): ex.copy(source,'../escape','bad')
    ex.copy(source,'.codex/policy.json','bad'); ex.finish('source',[])
    with pytest.raises(ValueError,match='non-research'): verify(ex.output)


def test_source_manifest_recovery_requires_exact_registered_bytes(tmp_path):
    import hashlib
    derived=tmp_path/'derived.csv'
    original=b'sample_id,depth_path,label\ns1,,1\n'
    derived.write_text('sample_id,depth_path,label\ns1,cache/s1.npy,1\n',encoding='utf-8')
    before=derived.read_bytes()
    destination=tmp_path/'source.csv'
    with pytest.raises(ValueError,match='byte-identically'):
        restore_source_manifest(derived,destination,'0'*64)
    assert not destination.exists()
    restore_source_manifest(derived,destination,hashlib.sha256(original).hexdigest())
    assert destination.read_bytes()==original
    assert derived.read_bytes()==before


@pytest.mark.parametrize('name',['.codex/hooks.json','.githooks/pre-commit',
    'scripts/project_hooks/runtime.py','scripts/project_inventory/cli.py',
    'tests/test_project_hooks.py','tests/test_project_inventory.py',
    'reports/marp_slides_tutorial/SKILL.md'])
def test_nonresearch_selection_is_explicit(name):
    assert excluded(name)
    assert excluded('src/deepface_pad/round7.py') is None
