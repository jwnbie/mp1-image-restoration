import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. FUNGSI PENGOLAHAN MANUAL (STRICTLY NUMPY) ---

def manual_median_filter(channel, size=5):
    """
    Menghilangkan noise salt-and-pepper yang padat.
    Kernel 5x5 lebih efektif membersihkan bintik besar daripada 3x3.
    """
    h, w = channel.shape
    pad = size // 2
    # Menggunakan padding 'reflect' agar tepi gambar tidak hitam/cacat
    padded = np.pad(channel, pad, mode='reflect')
    result = np.zeros((h, w))
    
    for i in range(h):
        for j in range(w):
            window = padded[i:i+size, j:j+size]
            # Mencari nilai tengah secara manual
            result[i, j] = np.median(window)
    return result.astype(np.uint8)

def manual_box_filter(channel, size=3):
    """
    Menghaluskan sisa Gaussian noise setelah median filter.
    Ini membuat tekstur kulit terlihat lebih 'clean' dan menyatu.
    """
    h, w = channel.shape
    pad = size // 2
    padded = np.pad(channel.astype(float), pad, mode='reflect')
    result = np.zeros((h, w))
    
    # Kernel rata-rata (box filter)
    kernel_val = 1.0 / (size * size)
    
    for i in range(h):
        for j in range(w):
            window = padded[i:i+size, j:j+size]
            result[i, j] = np.sum(window) * kernel_val
    return result.astype(np.uint8)

def manual_contrast_stretch(channel):
    """
    Memperbaiki contrast tanpa memperparah noise (lebih stabil dari HE).
    Memetakan intensitas 2% - 98% ke rentang 0-255.
    """
    # Mencari nilai percentile untuk menghindari outlier noise
    p_low, p_high = np.percentile(channel, (2, 98))
    
    # Rumus Stretching: (P - min) * (255 / (max - min))
    stretched = (channel.astype(float) - p_low) * (255.0 / (p_high - p_low))
    return np.clip(stretched, 0, 255).astype(np.uint8)

# --- 2. PIPELINE RESTORASI ---

def run_restoration():
    # Folder paths
    input_path = 'input/lena_noisy.png'
    output_path = 'output/lena_restored.png'
    
    # 1. Read Image (BGR)
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        print(f"Error: File {input_path} tidak ditemukan!")
        return

    print("Sedang merestorasi citra (tahap manual)...")

    # 2. Konversi ke YUV secara manual untuk menjaga warna asli
    # Y: Kecerahan, U & V: Warna
    img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(img_yuv)

    # 3. Denoising Tahap 1: Median Filter (Strong)
    # Dilakukan pada semua channel untuk membuang bintik warna
    print("- Membersihkan noise padat (Median 5x5)...")
    y = manual_median_filter(y, size=5)
    u = manual_median_filter(u, size=5)
    v = manual_median_filter(v, size=5)

    # 4. Denoising Tahap 2: Smoothing (Box Filter)
    # Membuat area kulit lebih mulus (clean)
    print("- Menghaluskan tekstur...")
    y = manual_box_filter(y, size=3)

    # 5. Contrast Enhancement
    print("- Memperbaiki kontras...")
    y_final = manual_contrast_stretch(y)

    # 6. Merge & Convert Back
    result_yuv = cv2.merge([y_final, u, v])
    result_bgr = cv2.cvtColor(result_yuv, cv2.COLOR_YUV2BGR)

    # 7. Save Result
    if not os.path.exists('output'):
        os.makedirs('output')
    cv2.imwrite(output_path, result_bgr)
    print(f"Restorasi selesai. Hasil disimpan di: {output_path}")

    # 8. Visualisasi dengan Matplotlib
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.title("Citra Rusak (Input)")
    plt.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.title("Hasil Restorasi (Clean)")
    plt.imshow(cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_restoration()