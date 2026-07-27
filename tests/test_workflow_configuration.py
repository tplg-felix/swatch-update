from pathlib import Path

WORKFLOW_PATH = Path(__file__).parents[1] / ".github" / "workflows" / "run-swatch-linker.yml"


def test_manual_workflow_exposes_required_inputs_and_report_artifact() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "matrixify_download_url:" in workflow
    assert "mode:" in workflow
    assert "live_confirmation:" in workflow
    assert "MATRIXIFY_DOWNLOAD_URL: ${{ inputs.matrixify_download_url }}" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "retention-days: 7" in workflow


def test_live_execution_requires_explicit_confirmation_in_workflow() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "--mode \"${{ inputs.mode }}\"" in workflow
    assert "--confirmation \"${{ inputs.live_confirmation }}\"" in workflow
