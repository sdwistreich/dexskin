# File name: visualize.py
# Author: Baiyu Shi
# Date last modified: 01/09/2025

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
import sys

# parameters
NUM_TAXELS = 120
timerDelay = 33  # ~30 Hz

# parameters defining visualization dot layout
finger_rows = 5
finger_cols = 12
gap = 4.0

positions = []

# visualization settings
min_val, max_val = 0.05, 1.0
min_dot_size = 10
max_dot_size = 150

# Right finger (positive x) on the right of GUI
for r in range(finger_rows):
    for c in range(finger_cols):
        x = c + gap / 2.0
        y = r - (finger_rows - 1) / 2.0
        positions.append([x, y])

# Left finger (negative x) on the left of GUI
for r in range(finger_rows):
    for c in range(finger_cols):
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

        self.t = 0.0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_scatter)
        self.timer.start(timerDelay)

    def get_simulated_frame(self):
        frame = np.zeros(NUM_TAXELS, dtype=np.float32)

        # variable-speed phase
        phase = self.t + 0.15 * np.sin(0.22 * self.t)

        # ---------- right finger: drag from top-left toward middle ----------
        progress = 0.5 + 0.5 * np.sin(0.45 * phase)   # 0 -> 1 -> 0
        right_center_col = 0.8 + 5.0 * progress       # left side to about middle
        right_center_row = 0.4 + 1.8 * progress       # top toward middle rows

        right_amplitude = 0.22 + 0.05 * np.sin(1.1 * phase)
        right_col_sigma = 0.85 + 0.12 * np.sin(0.7 * phase)
        right_row_sigma = 2.8

        idx = 0
        for r in range(finger_rows):
            for c in range(finger_cols):
                val = right_amplitude * np.exp(
                    -((c - right_center_col) ** 2) / (2 * right_col_sigma ** 2)
                    -((r - right_center_row) ** 2) / (2 * right_row_sigma ** 2)
                )
                val += 0.008 * np.random.rand()
                frame[idx] = val
                idx += 1

        # ---------- left finger: a couple of drifting presses ----------
        left_press_1_col = 3.0 + 0.45 * np.sin(0.9 * phase) + 0.15 * np.sin(2.0 * phase)
        left_press_1_row = 1.0 + 0.35 * np.sin(0.8 * phase)

        left_press_2_col = 8.0 + 0.5 * np.sin(0.7 * phase + 1.2) + 0.12 * np.sin(1.8 * phase)
        left_press_2_row = 3.2 + 0.3 * np.sin(0.85 * phase + 0.7)

        amp1 = 0.15 + 0.04 * np.sin(1.3 * phase)
        amp2 = 0.12 + 0.03 * np.sin(1.0 * phase + 0.5)

        sigma1_c, sigma1_r = 0.75, 0.75
        sigma2_c, sigma2_r = 0.9, 0.8

        for r in range(finger_rows):
            for c in range(finger_cols):
                val1 = amp1 * np.exp(
                    -((c - left_press_1_col) ** 2) / (2 * sigma1_c ** 2)
                    -((r - left_press_1_row) ** 2) / (2 * sigma1_r ** 2)
                )
                val2 = amp2 * np.exp(
                    -((c - left_press_2_col) ** 2) / (2 * sigma2_c ** 2)
                    -((r - left_press_2_row) ** 2) / (2 * sigma2_r ** 2)
                )

                val = val1 + val2 + 0.008 * np.random.rand()
                frame[idx] = val
                idx += 1

        self.t += 0.2
        return frame

    def update_scatter(self):
        flat_frame = self.get_simulated_frame()

        clipped = np.clip(flat_frame, min_val, max_val)
        normalized = (clipped - min_val) / (max_val - min_val)
        sizes = min_dot_size + normalized * (max_dot_size - min_dot_size)

        self.scatter.setData(
            pos=positions,
            size=sizes,
            brush=pg.mkBrush(255, 255, 255),
            pen=pg.mkPen(None)
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = DualFingerVisualization()
    win.show()
    sys.exit(app.exec_())