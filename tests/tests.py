import pytest
import subprocess
import os

filenames = ['ZRC_ENT00004017 Dorsal.CR2', 'ZRC_ENT00004017 Ventral.CR2', 'ZRC_ENT00004018 Dorsal.CR2', 'ZRC_ENT00004018 Ventral.CR2', 'ZRC_ENT00004135 A.CR2', 'ZRC_ENT00004910 Dorsal.CR2', 'ZRC_ENT00004910 Ventral(1).CR2', 'ZRC_ENT00004910 Ventral.CR2', 'ZRC_ENT00004105 Ventral.CR2', 'ZRC_ENT00026332 Dorsal.CR2', 'ZRC_ENT00026331 Ventral.CR2']


def test_renamed_files_correct():
    subprocess.run(['python', 'ocr_renamer.py'])
    directory = os.getcwd()
    files = [filename for filename in os.listdir(
        directory) if filename.endswith(".CR2")]
    assert set(files) == set(filenames)


