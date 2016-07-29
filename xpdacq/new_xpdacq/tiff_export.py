import numpy as np
from databroker import DataBroker as db
from bluesky.callbacks.broker import LiveTiffExporter

class xpdAcqSubtractedTiffExporter(LiveTiffExporter):
    "Intercept images before saving and subtract dark image"
    def start(self, doc):
        # The metadata refers to the scan uid of the dark scan.
        #if 'dark_frame' not in doc:
        dark_sub = True
        if 'dark_frame' not in doc:
            if 'sc_dk_field_uid' not in doc:
                raise ValueError("No dark_frame was recorded.")
            uid = doc['sc_dk_field_uid']
            dark_header = db[uid]
            self.dark_img, = db.get_images(db[uid], 'pe1_image')
        elif 'dark_frame'in doc:
            print('WOOOP, dark frame')
        super().start(doc)

    def event(self, doc):
        if self.field not in doc['data']:
            raise KeyError('required field = {} is not in header'.format(self.field))
            return

        db.fill_event(doc)  # modifies in place

        image = np.asarray(doc['data'][self.field])
        image = np.clip(image - self.dark_img, 0, None)
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

xpdacq_template = "/home/xf28id1/xpdUser/{start.sa_name}_{start.time}_{start.uid}_step{event.seq_num}.tif"
xpdacq_exporter = xpdAcqSubtractedTiffExporter('pe1_image', xpdacq_template)
