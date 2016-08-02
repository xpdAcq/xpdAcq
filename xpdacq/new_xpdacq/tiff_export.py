import os
import numpy as np
from databroker import DataBroker as db
from bluesky.callbacks.broker import LiveTiffExporter

class xpdAcqSubtractedTiffExporter(LiveTiffExporter):
    "Intercept images before saving and subtract dark image"
    def start(self, doc):
        # The metadata refers to the scan uid of the dark scan.
        dark_sub = True
        if 'dark_frame' not in doc:
            if 'sc_dk_field_uid' in doc:
                self.dark_uid = doc['sc_dk_field_uid']
            else:
                print("No dark_frame was associated in this scan."
                      "no subtraction will be performed")
                self.dark_uid = None
        elif 'dark_frame'in doc:
            self.dark_uid = None # found a dark frame
        super().start(doc)

    def _save_image(self, image, filename):
        base_name = os.path.split(filename)[0]
        base_name += '/'
        os.makedirs(base_name, exist_ok=True)
        super()._save_image(image, filename)

    def event(self, doc):
        if self.field not in doc['data']:
            raise KeyError('required field = {} is not in header'
                           .format(self.field))

        db.fill_event(doc)  # modifies in place
        image = np.asarray(doc['data'][self.field])
        if self.dark_uid is not None:
            dark_header = db[self.dark_uid]
            dark_img = db.get_images(dark_header, self.field)
        dark_img = np.zeros_like(image)
        image = np.clip(image - dark_img, 0, None)
        if image.ndim == 2:
            filename = self.template.format(start=self._start, event=doc)
            self._save_image(image, filename)
        if image.ndim == 3:
            for i, plane in enumerate(image):
                filename = self.template.format(i=i, start=self._start,
                                                event=doc)
                self._save_image(plane, filename)
        return filename
        # Don't call super() because that tries to fill_event again.

#xpdacq_template = "/home/xf28id1/xpdUser/tiff_base/{start.sa_name}_{start.time}_{start.uid}_step{event.seq_num}.tif"
#xpdacq_exporter = xpdAcqSubtractedTiffExporter('pe1_image', xpdacq_template)
