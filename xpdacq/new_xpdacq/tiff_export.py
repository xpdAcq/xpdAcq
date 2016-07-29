from time import sleep
import numpy as np
from bluesky.callbacks.broker import LiveTiffExporter
from .glbl import glbl

class SubtractedTiffExporter(LiveTiffExporter):
    "Intercept images before saving and subtract dark image"

    def start(self, doc):
        # The metadata refers to the scan uid of the dark scan.
        #if 'dark_frame' not in doc:
        if 'dark_frame' not in doc:
            if 'sc_dk_field_uid' not in doc:
                raise ValueError("No dark_frame was recorded.")
            uid = doc['sc_dk_field_uid']
            dark_header = glbl.db[uid]
            self.dark_img, = glbl.get_images(glbl.db[uid], 'pe1_image')
        elif 'dark_frame'in doc:
            print('WOOOP, dark frame')
            self.dark_img = np.zeros((2048,2048))
        super().start(doc)

    def event(self, doc):
        img = doc['data'][self.field]
        subtracted_img = img - self.dark_img
        doc['data'][self.field] = subtracted_img
        super().event(doc)

xpd_template = "/home/xf28id1/xpdUser/tiff_base/{start.sa_name}/{start.time}_{start.uid}_step{event.seq_num}.tif"
xpd_exporter = SubtractedTiffExporter('pe1_image', xpd_template)
