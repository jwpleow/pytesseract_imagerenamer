"""
This script renames the .CR2 images in the current working directory by their label (using Tesseract OCR) and D/V tag (using template matching)

long label or label refers to the long string label e.g. ZRC_ENT00004097
"""

import os
import sys
import time
from multiprocessing import Lock, Pool, Manager, Value
from functools import partial
import renamer
from renamer import CWD, FileExtension

print = partial(print, flush=True)

def ProcessImage(filename) -> bool:
    renameObj = renamer.ImageRenamerCR2(filename, globalFileLock)
    if renameObj.Process():
        globalRenamedFileCounter.value += 1
        return True
    else:
        globalUnrenamedFileList.append(filename)
        return False

# to initialise the global variables into the processor pool
def init(lock, unrenamedFileList, renamedFileCounter):
    global globalFileLock
    global globalUnrenamedFileList
    global globalRenamedFileCounter
    globalFileLock = lock
    globalUnrenamedFileList = unrenamedFileList
    globalRenamedFileCounter = renamedFileCounter

if __name__ == '__main__':
    start = time.time()
    print("Looking at images...")
    fileLock = Lock()
    manager = Manager()
    unrenamedFiles = manager.list()  # holds shared list of unrenamed files during first round of processing
    renamedFileCounter = Value('i', 0)

    files = [filename for filename in sorted(os.listdir(CWD)) if (filename.endswith(FileExtension) and not filename.startswith('ZRC_ENT'))]
    no_of_files = len(files)

    pool = Pool(initializer=init, initargs=(fileLock, unrenamedFiles, renamedFileCounter))
    try:
        pool.map_async(ProcessImage, files).get(99999)
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()
        print("Shutting down program...")
        sys.exit(1)
    pool.close()
    pool.join()

    print(f"The script took {(time.time() - start):.1f}s to rename {renamedFileCounter.value} out of {no_of_files} files.")
    if unrenamedFiles:
        print(f"The files that could not be renamed are:")
        print(unrenamedFiles)
