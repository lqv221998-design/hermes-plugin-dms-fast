import unittest
import test_reader as reader
from pathlib import Path

class SetupSkillRegistration(unittest.TestCase):
 def test_setup_guidance_is_discoverable_without_browser_or_install(self):
  ctx=reader.ReaderTests().context();reader.plugin.register(ctx)
  skills={c.args[0]:Path(c.args[1]) for c in ctx.register_skill.call_args_list}
  self.assertIn('setup',skills,'Recipient onboarding must be registered, not only an unreferenced README')
  self.assertTrue(skills['setup'].is_file())
  self.assertTrue(skills['reading'].is_file())
  ctx.call_mcp.assert_not_called()
 def test_native_guidance_routes_missing_mcp_to_setup_skill(self):
  ctx=reader.ReaderTests().context();reader.plugin.register(ctx)
  hooks={c.args[0]:c.args[1] for c in ctx.register_hook.call_args_list}
  text=hooks['pre_llm_call']()['context']
  self.assertIn('dms-fast:setup',text)
  ctx.call_mcp.assert_not_called()

if __name__=='__main__':unittest.main()
