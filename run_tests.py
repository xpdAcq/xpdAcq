#!/usr/bin/env python
import sys
import pytest

if __name__ == '__main__':
    from xpdsim.dets import nsls_ii_path
    print(nsls_ii_path)
    # show output results from every test function
    args = ['-v', '-vrxs']
    # show the message output for skipped and expected failure tests
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    print('pytest arguments: {}'.format(args))
    # # compute coverage stats for xpdAcq
    # args.extend(['--cov', 'xpdAcq'])
    # call pytest and exit with the return code from pytest so that
    # travis will fail correctly if tests fail
    sys.exit(pytest.main(args))
