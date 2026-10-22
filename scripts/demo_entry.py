"""Bundled demo entry point uses disposable sample data only."""
import sys
from EdgeProfileOrg_GUI import main

if __name__ == '__main__':
    sys.argv = [sys.argv[0], '--demo'] + sys.argv[1:]
    main()
