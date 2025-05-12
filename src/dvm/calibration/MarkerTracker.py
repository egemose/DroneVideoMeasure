"""
Marker tracker for locating n-fold edges in images using convolution.

@author: Henrik Skov Midtiby
"""

from __future__ import annotations

import cv2
import numpy as np


class MarkerTracker:
    """Purpose: Locate a certain marker in an image."""

    def __init__(self, order: int, kernel_size: int, scale_factor: float) -> None:
        self.kernel_size = kernel_size
        (kernel_real, kernel_imag) = self.generate_symmetry_detector_kernel(order, kernel_size)

        self.order = order
        self.mat_real = kernel_real / scale_factor
        self.mat_imag = kernel_imag / scale_factor

        self.frame_real: np.ndarray
        self.frame_imag: np.ndarray
        self.frame_sum_squared: np.ndarray

    @staticmethod
    def generate_symmetry_detector_kernel(order: int, kernel_size: int) -> tuple[np.ndarray, np.ndarray]:
        value_range = np.linspace(-1, 1, kernel_size)
        temp1 = np.meshgrid(value_range, value_range)
        kernel = temp1[0] + 1j * temp1[1]

        magnitude = abs(kernel)
        kernel = np.power(kernel, order)
        kernel = kernel * np.exp(-8 * magnitude**2)

        return np.real(kernel), np.imag(kernel)

    def apply_convolution_with_complex_kernel(self, frame: np.ndarray) -> np.ndarray:
        self.frame_real = frame.copy()
        self.frame_imag = frame.copy()

        # Calculate convolution and determine response strength.
        self.frame_real = cv2.filter2D(self.frame_real, cv2.CV_32F, self.mat_real)
        self.frame_imag = cv2.filter2D(self.frame_imag, cv2.CV_32F, self.mat_imag)
        frame_real_squared = cv2.multiply(self.frame_real, self.frame_real, dtype=cv2.CV_32F)
        frame_imag_squared = cv2.multiply(self.frame_imag, self.frame_imag, dtype=cv2.CV_32F)
        self.frame_sum_squared = cv2.add(frame_real_squared, frame_imag_squared, dtype=cv2.CV_32F)
        return self.frame_sum_squared
