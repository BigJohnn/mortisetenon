import unittest
from check_cad_privacy import reason


class PrivacyRules(unittest.TestCase):
    def test_protected(self):
        for path in ['.env','nested/.env.local','cad/private/new-node/build.py','cad/private/new-node/parameters.json','cad/table-node-pair_freecad_v0.2/notes.md','draft.FCSTD','draft.FCStd1','test.STEP','print.STL','preview.GLTF','cad/new.fs','cad/new.scad','tools/build_table_nodes_freecad.py']:
            self.assertIsNotNone(reason(path),path)

    def test_public_review_inputs(self):
        for path in ['content/cross_lap_cad_status_v0.1.json','assets/images/cross-lap-tenon/v0.1/nominal_assembled.webp','cad/cross-lap-tenon.html','CAD_PRIVACY.md']:
            self.assertIsNone(reason(path),path)


if __name__=='__main__':unittest.main()
