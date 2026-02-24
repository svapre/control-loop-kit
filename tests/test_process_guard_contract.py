from control_loop.policy import load_policy
from control_loop.process_guard import evaluate_change_coupling


def test_process_vs_project_fields_loaded_from_policy():
    policy = load_policy()
    process_fields = policy["process_guard"]["process_guideline_fields"]
    project_fields = policy["process_guard"]["project_guideline_fields"]

    assert "- Selected work mode:" in process_fields
    assert "- Structural correctness:" in project_fields


def test_process_change_requires_changelog_update():
    policy = load_policy()
    failures = evaluate_change_coupling({"SPEC.md"}, policy)

    assert any("PROCESS_CHANGELOG" in item for item in failures)

