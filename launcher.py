# PyInstaller entry point: running labelme/__main__.py directly breaks its
# relative imports, so import the package normally and invoke main().
import multiprocessing

from labelme.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
