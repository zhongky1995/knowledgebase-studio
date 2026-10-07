"""Design receipt and example generation regressions; not visual quality judgments."""
import copy
import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from kb_visual_check import check_visuals, DESIGN_DIMENSIONS
from kb_visual_examples import examples
from test_knowledgebase_studio import valid_visual_manifest


def png(width,height=10):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+b'\xff'*(width*3))*height))+chunk(b'IEND',b'')


class VisualDesignTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();(self.root/'assets').mkdir();(self.root/'_kb-control').mkdir()
        self.manifest=valid_visual_manifest();self.manifest['schemaVersion']=2
        self.item=self.manifest['items'][0]
        self.asset=self.root/self.item['assetPath'];self.asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 500"><text x="20" y="30" font-size="18">Synthetic</text></svg>')
        (self.root/'lesson.md').write_text(f"![{self.item['altText']}]({self.item['assetPath']})")
        self.review={'pattern':'before-after','designSystem':'Synthetic test fixture','minLabelPxTarget':14,'assetSha256':{self.item['assetPath']:hashlib.sha256(self.asset.read_bytes()).hexdigest()},'dimensions':{k:{'status':'pass','observation':'Synthetic structural receipt, not an actual browser observation.'} for k in DESIGN_DIMENSIONS},'viewports':[]}
        for width,rendered in [(390,320),(1280,360)]:
            path=self.root/'_kb-control'/f'{width}.png';path.write_bytes(png(rendered))
            self.review['viewports'].append({'viewportWidth':width,'renderedWidth':rendered,'minLabelPx':16,'captureScale':1,'screenshotPath':str(path.relative_to(self.root)),'screenshotSha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        self.item['designReview']=self.review

    def check(self):
        (self.root/'_kb-control/visual-explanations.json').write_text(json.dumps(self.manifest))
        return check_visuals(self.root)

    def fails(self,kind):
        result=self.check();self.assertEqual(result['status'],'fail');self.assertIn(kind,{e['kind'] for e in result['errors']})

    def test_complete_receipt_passes(self):
        self.assertEqual(self.check()['status'],'pass')

    def test_new_schema_requires_design_review(self):
        del self.item['designReview'];self.fails('visual-design-review')

    def test_asset_change_stales_receipt(self):
        self.asset.write_text(self.asset.read_text().replace('Synthetic','Changed'))
        self.fails('visual-design-stale')

    def test_screenshot_change_stales_receipt(self):
        (self.root/self.review['viewports'][0]['screenshotPath']).write_bytes(png(320,20))
        self.fails('visual-screenshot-stale')

    def test_mobile_capture_required(self):
        self.review['viewports']=self.review['viewports'][1:];self.fails('visual-viewports')

    def test_undersized_labels_fail(self):
        self.review['viewports'][0]['minLabelPx']=11;self.fails('visual-small-label')

    def test_falsely_recorded_image_size_fails(self):
        self.review['viewports'][0]['renderedWidth']=300;self.fails('visual-capture-size')

    def test_missing_design_dimension_fails(self):
        del self.review['dimensions']['connections'];self.fails('visual-design-dimension')

    def test_design_failure_cannot_hide_behind_manifest_pass(self):
        self.review['dimensions']['mechanismVisibility']['status']='fail';self.fails('visual-design-dimension')

    def test_small_type_exception_requires_reason(self):
        self.review['minLabelPxTarget']=12;self.fails('visual-label-exception')

    def test_nonfinite_and_boolean_measurements_fail(self):
        for value in [True,float('nan'),float('inf')]:
            with self.subTest(value=value):
                self.review['viewports'][0]['minLabelPx']=value;self.fails('visual-viewport')

    def test_missing_screenshot_fails(self):
        (self.root/self.review['viewports'][0]['screenshotPath']).unlink();self.fails('missing-file')

    def test_legacy_manifest_remains_compatible_but_explicit(self):
        self.manifest['schemaVersion']=1;del self.item['designReview']
        result=self.check();self.assertEqual(result['status'],'pass')
        self.assertIn('legacy-visual-design',{w['kind'] for w in result['warnings']})

    def test_screenshot_is_in_workflow_fingerprint(self):
        from kb_workflow import stage_deliverable_digests
        self.check()
        path=self.review['viewports'][0]['screenshotPath']
        before=stage_deliverable_digests(self.root,'content')
        self.assertIn(path,before)
        (self.root/path).write_bytes(png(320,12))
        after=stage_deliverable_digests(self.root,'content')
        self.assertNotEqual(before[path],after[path])

    def test_examples_are_self_contained_and_editable(self):
        import xml.etree.ElementTree as ET
        files=examples();self.assertEqual(len(files),9)
        for name,body in files.items():
            if name.endswith('.svg'):
                svg=ET.fromstring(body)
                self.assertEqual(svg.get('viewBox'),'0 0 360 500')
                self.assertTrue(svg.findall('.//{http://www.w3.org/2000/svg}text'))
                self.assertNotIn('<image',body)
        self.assertNotEqual(files['shared-boundary-bad.svg'],files['request-reply-bad.svg'])


if __name__=='__main__':unittest.main()
