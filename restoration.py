import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. FUNGSI PENGOLAHAN MANUAL (STRICTLY NUMPY) ---

def manual_median_filter(channel, size=3):
    h, w = channel.shape
    pad = size // 2
    padded = np.pad(channel, pad, mode='reflect')
    result = np.zeros((h, w))
    for i in range(h):
        for j in range(w):
            result[i, j] = np.median(padded[i:i+size, j:j+size])
    return result.astype(np.uint8)

def manual_gaussian_blur(channel, size=5, sigma=1.0):
    h, w = channel.shape
    pad = size // 2
    x = np.linspace(-pad, pad, size)
    kern1d = np.exp(-np.square(x) / (2 * np.square(sigma)))
    kernel = np.outer(kern1d, kern1d)
    kernel /= kernel.sum()
    padded = np.pad(channel.astype(float), pad, mode='reflect')
    result = np.zeros((h, w))
    for i in range(h):
        for j in range(w):
            result[i, j] = np.sum(padded[i:i+size, j:j+size] * kernel)
    return result.astype(np.uint8)

def manual_histogram_equalization(channel):
    hist, bins = np.histogram(channel.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    # Normalisasi CDF ke rentang 0-255
    cdf_m = (cdf - cdf.min()) * 255 / (channel.size - cdf.min())
    return cdf_m[channel].astype(np.uint8)

def manual_unsharp_masking(channel, amount=1.0):
    """Sharpening untuk mengembalikan detail tajam."""
    blurred = manual_gaussian_blur(channel, size=5, sigma=1.0)
    sharpened = channel.astype(float) + amount * (channel.astype(float) - blurred.astype(float))
    return np.clip(sharpened, 0, 255).astype(np.uint8)

# --- 2. PIPELINE UTAMA & TRACKING TAHAPAN ---

def run_restoration():
    input_path = 'input/lena_noisy.png'
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        print(f"Error: {input_path} tidak ditemukan!")
        return

    # List untuk menyimpan state tiap tahap: [B, G, R]
    steps = []
    b, g, r = cv2.split(img_bgr)
    steps.append([b, g, r]) # Step 0: Original

    print("Step 1: Median Filtering (Denoising)...")
    b = manual_median_filter(b, 3)
    g = manual_median_filter(g, 3)
    r = manual_median_filter(r, 3)
    steps.append([b, g, r])

    print("Step 2: Gaussian Smoothing...")
    b = manual_gaussian_blur(b, 5, 0.8)
    g = manual_gaussian_blur(g, 5, 0.8)
    r = manual_gaussian_blur(r, 5, 0.8)
    steps.append([b, g, r])

    print("Step 3: Histogram Equalization (Contrast)...")
    b = manual_histogram_equalization(b)
    g = manual_histogram_equalization(g)
    r = manual_histogram_equalization(r)
    steps.append([b, g, r])

    print("Step 4: Unsharp Masking (Sharpening)...")
    b = manual_unsharp_masking(b, 0.8)
    g = manual_unsharp_masking(g, 0.8)
    r = manual_unsharp_masking(r, 0.8)
    steps.append([b, g, r])

    # Save Final Result
    final_bgr = cv2.merge([b, g, r])
    if not os.path.exists('output'): os.makedirs('output')
    cv2.imwrite('output/lena_restored.png', final_bgr)

    # --- 3. VISUALISASI ANALISIS HISTOGRAM ---
    
    fig, axes = plt.subplots(5, 3, figsize=(18, 22))
    titles = ["Original Noisy", "Step 1: Median", "Step 2: Gaussian", "Step 3: Hist EQ", "Step 4: Sharpen"]
    colors = ['#4A90E2', '#50C878', '#E34234'] # Blue, Green, Red
    channel_names = ['Blue', 'Green', 'Red']

    for i in range(5):
        for j in range(3):
            ax = axes[i, j]
            data = steps[i][j]
            
            # Hitung statistik manual
            mu = np.mean(data)
            sigma = np.std(data)
            
            # Plot Hist
            hist, _ = np.histogram(data.flatten(), 256, [0, 256])
            ax.bar(range(256), hist, color=colors[j], alpha=0.7, width=1.0)
            
            # Garis Mean
            ax.axvline(mu, color='black', linestyle='--', linewidth=1)
            
            # Labeling
            ax.set_title(f"{titles[i]} - {channel_names[j]}", fontsize=10, fontweight='bold')
            ax.text(0.05, 0.9, f'$\mu={mu:.1f}$\n$\sigma={sigma:.1f}$', 
                    transform=ax.transAxes, fontsize=9, verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.6))
            
            ax.set_xlim([0, 255])
            ax.tick_params(axis='both', labelsize=8)
            ax.grid(axis='y', linestyle=':', alpha=0.3)

    plt.subplots_adjust(left=0.07, bottom=0.05, right=0.95, top=0.94, wspace=0.25, hspace=0.4)
    plt.suptitle("Analisis Histogram RGB per Tahapan Pipeline Restorasi", fontsize=16, fontweight='bold', y=0.98)
    plt.savefig('output/histogram_step_by_step.png', dpi=300)
    plt.show()

    # --- 4. FIGURE STEP-BY-STEP VISUALIZATION (TAMBAHAN) ---
    
    plt.figure("Analisis Perubahan Citra per Tahap", figsize=(18, 5))
    step_titles = [
        "1. Original Noisy", 
        "2. After Median (Denoise)", 
        "3. After Gaussian (Smooth)", 
        "4. After Hist EQ (Contrast)", 
        "5. Final (Sharpened)"
    ]
    
    for i in range(5):
        plt.subplot(1, 5, i+1)
        # Gabungkan B, G, R untuk setiap step dan ubah ke RGB untuk Matplotlib
        step_bgr = cv2.merge([steps[i][0], steps[i][1], steps[i][2]])
        step_rgb = cv2.cvtColor(step_bgr, cv2.COLOR_BGR2RGB)
        
        plt.imshow(step_rgb)
        plt.title(step_titles[i], fontsize=10, fontweight='bold')
        plt.axis('off')
    
    plt.subplots_adjust(wspace=0.1, left=0.02, right=0.98)
    plt.savefig('output/visual_step_by_step.png', dpi=300) # Disimpan otomatis
    plt.show()
    
    # --- 5. FIGURE PERBANDINGAN AKHIR ---
    
    plt.figure("Hasil Akhir Restorasi", figsize=(14, 7))
    plt.subplot(1, 2, 1)
    plt.title("Input (Noisy)")
    plt.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.title("Output (Restored & Sharpened)")
    plt.imshow(cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_restoration()