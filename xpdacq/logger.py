"""module to create centralize logger"""
import os
import time
import logging

from .xpdacq_conf import glbl_dict

# this module only gets imported when profile is loaded
logger = logging.getLogger("xpdAcq_main")
logger.setLevel(logging.INFO)  # set threhold 

# configure logging format
fh = logging.FileHandler(glbl_dict['logging_path'])
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)


logger.info("xpdAcq started")
