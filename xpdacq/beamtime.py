class Beamtime(object):
    def __init__(self, stem):
        self.stem = stem


    @property
    def B_DIR(self):
        # FIXME: confirm where to put backup dir
        return os.path.expanduser('~/xpdBackup') # remote backup directory
