import pytest
import subprocess
import os

filenames = ['ZRC_ENT00004017 D.CR2', 'ZRC_ENT00004017 V.CR2', 'ZRC_ENT00004018 D.CR2', 'ZRC_ENT00004018 V.CR2', 'ZRC_ENT00004135 A.CR2', 'ZRC_ENT00004910 D.CR2', 'ZRC_ENT00004910 V(1).CR2', 'ZRC_ENT00004910 V.CR2', 'ZRC_ENT00004105 V.CR2']


def test_renamed_files_correct():
    subprocess.run(['python', 'ocr_renamer.py'])
    directory = os.getcwd()
    files = [filename for filename in os.listdir(
        directory) if filename.endswith(".CR2")]
    assert set(files) == set(filenames)


