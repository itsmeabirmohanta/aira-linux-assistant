## Description
Briefly describe the intent and architecture of this change.

## Related Issues
Fixes #(issue number)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change adding tool or capability)
- [ ] UI / Design update (Swiss Modernism 2.0 aesthetics)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update (DPDP compliance, permissions, guides)

## Testing Performed
- [ ] Subsystem & ReAct simulation: `.venv/bin/python tests/simulate_full_workflow.py`
- [ ] GUI layout offscreen test: `QT_QPA_PLATFORM=offscreen .venv/bin/python tests/test_gui_instantiation.py`
- [ ] Manual test in Wayland or X11 desktop environment

## Checklist
- [ ] My code follows the Swiss Modernism 2.0 UI aesthetic and PEP 8 guidelines.
- [ ] I have added tests that prove my fix is effective or that my feature works.
- [ ] I have updated documentation where appropriate (README, PERMISSIONS, PRIVACY_DPDP).
- [ ] Zero telemetry guarantees and DPDP privacy principles are strictly maintained.
