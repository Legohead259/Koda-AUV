from pgmpy.readwrite import BIFReader

reader = BIFReader("auto/model/barrel_model.bif")
model = reader.get_model()