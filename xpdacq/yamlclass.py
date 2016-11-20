import os
import yaml

class YamlClass:
    """special class automatically yamlize user-defined attributes
    if they are updated"""
    def __init__(self, internal_dict={}):
        # dict stores values of valid attributes
        self._internal_dict = internal_dict
        for key in self.allowed_attributes():
            try:
                val = self.__getattribute__(str(key))
                self._internal_dict.update({key:val})
            except AttributeError:
                print("pass {}".format(key))

    def __setattr__(self, key, val):
        if key in self.allowed_attributes():
            self._internal_dict.update({key: val})
            self.flush()
        super().__setattr__(key, val)

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, fpath):
        """setter to create file if it doesn't exist"""
        self._filepath = fpath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        print("filepath is about to be flushed")
        self.flush()

    def allowed_attributes(self):
        pass

    def flush(self):
        """method to yamlize allowed attributes"""
        with open(self._filepath, 'w') as f:
            yaml.dump(self._internal_dict, f, default_flow_style=False)
