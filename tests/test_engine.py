from strideai.core.models import DetectedComponent
from strideai.stride.engine import analyze


def det(component_type: str, conf: float = 0.9) -> DetectedComponent:
    return DetectedComponent(component_type=component_type, confidence=conf, bbox=(0, 0, 10, 10))


def test_empty_detections_yield_empty_model():
    tm = analyze([])
    assert tm.components == []


def test_deduplicates_and_counts_instances():
    tm = analyze([det("load_balancer"), det("load_balancer"), det("load_balancer")])
    assert len(tm.components) == 1
    assert tm.components[0].component_type == "load_balancer"
    assert tm.components[0].instance_count == 3
    assert len(tm.components[0].threats) >= 1


def test_components_ordered_canonically():
    tm = analyze([det("database"), det("user")])
    assert [c.component_type for c in tm.components] == ["user", "database"]


def test_rule_database_without_waf():
    tm = analyze([det("database")])
    assert any("WAF" in w or "firewall" in w.lower() for w in tm.architecture_warnings)


def test_rule_not_fired_when_waf_present():
    tm = analyze([det("database"), det("firewall_waf")])
    assert not any("WAF" in w or "firewall" in w.lower() for w in tm.architecture_warnings)


def test_rule_user_without_auth_service():
    tm = analyze([det("user")])
    assert any("autentica" in w.lower() for w in tm.architecture_warnings)


def test_rule_external_service_trust_boundary():
    tm = analyze([det("external_service")])
    assert any("confian" in w.lower() for w in tm.architecture_warnings)
