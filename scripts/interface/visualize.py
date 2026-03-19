# File name: Visualization_120taxels_pcap_dot_dual.py
# Author: Baiyu Shi
# Date last modified: 01/09/2025

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import multiprocessing.shared_memory as shm

#parameters.
SHM_NAME = 'dexskin_memory'  # Shared memory block name
NUM_TAXELS = 120             # Total number of taxels (5*12*2)
timerDelay = 33             #33ms updates for 30Hz update.

#parameters defining visualization dot layout.
finger_rows = 5
finger_cols = 12
gap = 4.0

positions = []

#visualization settings
min_val, max_val = 0.05, 1.0
min_dot_size = 10
max_dot_size = 150

# Right finger (positive x) on the right of GUI
for r in range(finger_rows):
    for c in range(finger_cols):
        # x starts from gap/2, y is centered vertically around 0
        x = c + gap / 2.0
        y = r - (finger_rows - 1) / 2.0
        positions.append([x, y])

# Left finger (negative x) on the left of GUI.
for r in range(finger_rows):
    for c in range(finger_cols):
        # x starts from -gap/2 and goes left, creating a mirror image
        x = -(c + gap / 2.0)
        y = r - (finger_rows - 1) / 2.0
        positions.append([x, y])

positions = np.array(positions)
assert len(positions) == NUM_TAXELS, "Position array length must match NUM_TAXELS"


class DualFingerVisualization(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DexSkin Tactile Data Visualization')
        self.resize(800, 600)

        try:
            self.shm = shm.SharedMemory(name=SHM_NAME)
            self.frame_buffer = np.ndarray(
                (NUM_TAXELS,), dtype=np.float32, buffer=self.shm.buf
            )
            print(f"Attached to shared memory: {SHM_NAME}")
        except FileNotFoundError:
            print(f"ERROR: Shared memory block '{SHM_NAME}' not found.")
            print("Please ensure the data providing script is running.")
            sys.exit(1)

        graphicswidget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(graphicswidget)
        
        view = graphicswidget.addViewBox()
        view.setAspectLocked(True)
        self.scatter = pg.ScatterPlotItem()
        view.addItem(self.scatter)

        min_x, min_y = positions.min(axis=0)
        max_x, max_y = positions.max(axis=0)

        view.invertY(True)

        padding = 1.0
        view.setRange(
            QtCore.QRectF(
                min_x - padding,
                min_y - padding,
                (max_x - min_x) + 2 * padding,
                (max_y - min_y) + 2 * padding
            )
        )
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_scatter)
        self.timer.start(timerDelay)

    def update_scatter(self):
        #getting the data from the shared frame buffer.
        flat_frame = self.frame_buffer.copy()

        clipped = np.clip(flat_frame, min_val, max_val)
        normalized = (clipped - min_val) / (max_val - min_val)
        sizes = min_dot_size + normalized * (max_dot_size - min_dot_size)

        self.scatter.setData(
            pos=positions,
            size=sizes,
            brush=pg.mkBrush(255, 255, 255),  
            pen=pg.mkPen(None)             
        )

    def closeEvent(self, event):
        """Clean up shared memory on window close."""
        print("Closing shared memory attachment.")
        self.shm.close()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = DualFingerVisualization()
    win.show()
    sys.exit(app.exec_())