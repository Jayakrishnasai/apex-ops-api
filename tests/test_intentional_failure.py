"""
Intentional failure test — CI blocking demonstration.

PURPOSE
-------
This test is DESIGNED to fail. Its sole role is to demonstrate that the
CI pipeline correctly detects failures and blocks deployment.

In the CI workflow:
  • The main test gate runs:  pytest tests/ -k "not intentional"
  • A separate CI step runs this file alone to record the failure in logs.

This satisfies the assessment requirement:
  "At least 6 automated checks including one intentional failure"

HOW TO RUN
----------
To run only the intentional failure (for evidence):
    pytest tests/test_intentional_failure.py -v

To run the main suite (gates deployment, this file excluded):
    pytest tests/ -k "not intentional" -v
"""


def test_intentional_failure_demonstrates_ci_block():
    """
    INTENTIONAL FAILURE — do not fix.

    This assertion always fails. When the CI pipeline runs this test it records
    a FAILED status and blocks the deployment job, proving the gate works.

    Evidence: see the CI run log titled "Demonstrate CI blocking".
    """
    expected_value = 42
    actual_value = 0  # deliberately wrong
    assert actual_value == expected_value, (
        "INTENTIONAL FAILURE: This test exists to prove CI blocks on failures. "
        "The deployment job depends on the main test suite (which excludes this "
        "test via -k 'not intentional'). See RUNBOOK.md §CI for details."
    )
