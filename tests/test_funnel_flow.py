import os
import tempfile
import unittest

# Set a test-only database before importing application modules.
_TEMP = tempfile.TemporaryDirectory()
os.environ["FUNNEL_DB_PATH"] = os.path.join(_TEMP.name, "test.db")

import core
import schemas

class FunnelFlowTests(unittest.TestCase):
    def test_end_to_end_export_and_analytics(self):
        f = core.create_funnel("Demo", "Lead generation")
        fid = f["funnel_id"]
        core.add_landing_page(fid, "Start here", "Free guide", "Learn more")
        core.add_optin_page(fid, "Get the guide", "Subscribe to learn more")
        core.add_thankyou_page(fid)
        self.assertEqual(len(core.get_funnel(fid)["pages"]), 3)
        core.record_event(fid, "visit")
        core.record_event(fid, "optin")
        analytics = core.get_funnel_analytics(fid)
        self.assertEqual(analytics["visits"], 1)
        self.assertEqual(analytics["optins"], 1)
        with tempfile.TemporaryDirectory() as tmp:
            output = core.publish_funnel(fid, tmp)
            self.assertEqual(len(output["pages"]), 3)
            for page in output["pages"]:
                self.assertTrue(os.path.isfile(page["file"]))
        core.delete_funnel(fid)

    def test_schema_tools_available(self):
        names = {x["name"] for x in schemas.TOOLS}
        self.assertEqual(len(names), 15)
        self.assertIn("publish_funnel", names)

if __name__ == "__main__":
    unittest.main()
