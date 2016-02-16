        '''
        # finds an extra directory so won't start
        os.mkdir(os.path.join(self.home_dir,'OldUserJunk')) 
        _start_beamtime(base_dir = self.base_dir)
        #self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        # finds an extra non-tar file so won't start
        self.tarfile = os.path.join(self.home_dir,'touched.tar')
        open(self.tarfile, 'a').close()
        self.assertTrue(os.path.isfile(self.tarfile))
        _start_beamtime(base_dir = self.base_dir)
        #self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        self.newfile = os.path.join(self.home_dir,'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        _start_beamtime(base_dir = self.base_dir)
        #self.assertRaises(RuntimeError, lambda:_start_beamtime(base_dir = self.base_dir))
        '''

    def test_start_beamtime(self):
        '''#cleanup!
        shutil.rmtree(self.home_dir)
        #_start_beamtime(base_dir = self.base_dir)
        '''