import sys

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="Currently Windows is not supported")
def test_smoke_end_to_end(hf_runner):
    hf_runner(task='language_modeling', dataset='wikitext', model='prajjwal1/bert-tiny')
