import unittest
import test_session as sessions


class StatusTests(unittest.TestCase):
    def test_status_reads_saved_attempt_without_browser_or_mutation(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        helper.prepare(ctx)
        ctx.state.set('download_one-qaqc', {'attempted': True, 'source': {'code': 'QT-KT-07'}})
        ctx.call_mcp.reset_mock()
        before = dict(ctx.state.values)
        result = helper.invoke(ctx, {'action': 'status', 'work_id': 'one-qaqc'})
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 'pending_work')
        self.assertEqual(result['plugin_version'], __import__(sessions.reader.plugin.__name__ + '.session', fromlist=['VERSION']).VERSION)
        self.assertTrue(result['download_attempted'])
        self.assertEqual(before, ctx.state.values)
        ctx.call_mcp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
