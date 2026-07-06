from strideai.core.models import COMPONENT_CLASSES, StrideCategory
from strideai.stride.kb import load_kb


def test_every_canonical_class_has_kb_entry():
    kb = load_kb()
    assert set(kb.keys()) == set(COMPONENT_CLASSES)


def test_every_entry_has_valid_threats():
    kb = load_kb()
    for name, threats in kb.items():
        assert len(threats) >= 1, name
        for t in threats:
            assert isinstance(t.category, StrideCategory)
            assert t.description.strip()
            assert len(t.countermeasures) >= 1
            assert all(c.strip() for c in t.countermeasures)


def test_kb_is_cached():
    assert load_kb() is load_kb()
