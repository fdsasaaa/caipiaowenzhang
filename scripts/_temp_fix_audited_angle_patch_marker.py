from pathlib import Path

path = Path("scripts/_temp_apply_audited_angle_contract_v1.py")
text = path.read_text(encoding="utf-8")
old = '''                    "multistage_score": multistage_score,\n                    "errors": approval.errors,\n'''
new = '''                    "multistage_score": multistage_score,\n                    "provider_response_id": response_id or None,\n                    "errors": approval.errors,\n'''
replacement = '''                    "multistage_score": multistage_score,\n                    "angle_score": getattr(approval, "angle_score", None),\n                    "provider_response_id": response_id or None,\n                    "errors": approval.errors,\n'''
assert old in text, "outdated approval_failed patch marker not found"
text = text.replace(old, new, 1)
assert new in text, "current controller approval_failed marker missing from patch script"
text = text.replace(new, replacement, 1)
# The replacement above must remain the NEW argument passed to replace_once(), not
# mutate the OLD argument. Rebuild that one call explicitly so runtime patches the
# current PR68-era controller into the angle-aware controller.
broken = '''replace_once(\n    "engine/production_controller.py",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"angle_score\\": getattr(approval, \\"angle_score\\", None),\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"angle_score\\": getattr(approval, \\"angle_score\\", None),\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n)'''
# The literal representation in the script uses ordinary quoted Python strings;
# repair it more directly with the exact post-edit call text if the naive edits
# touched both old/new values.
call_old = '''replace_once(\n    "engine/production_controller.py",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"angle_score\\": getattr(approval, \\"angle_score\\", None),\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"angle_score\\": getattr(approval, \\"angle_score\\", None),\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n)'''
call_new = '''replace_once(\n    "engine/production_controller.py",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n    "                    \\"multistage_score\\": multistage_score,\\n                    \\"angle_score\\": getattr(approval, \\"angle_score\\", None),\\n                    \\"provider_response_id\\": response_id or None,\\n                    \\"errors\\": approval.errors,\\n",\n)'''
if call_old in text:
    text = text.replace(call_old, call_new, 1)
path.write_text(text, encoding="utf-8")
print("controller approval_failed patch marker updated for PR68 response-id field")
