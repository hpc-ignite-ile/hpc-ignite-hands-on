#!/usr/bin/env python3
"""
CuPy Basics - พื้นฐาน CuPy
Chapter 10: GPU Programming

CuPy = NumPy-compatible GPU arrays
"""

import time
import numpy as np

# Check if CuPy is available
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    print("CuPy not installed. Use a prebuilt project CuPy environment for live LANTA training.")
    print("Running in demo mode (NumPy only)")


def compare_array_creation():
    """เปรียบเทียบการสร้าง array"""
    print("\n1. Array Creation:")

    size = (5000, 5000)

    # NumPy (CPU)
    start = time.time()
    cpu_array = np.random.random(size)
    cpu_time = time.time() - start
    print(f"   NumPy: {cpu_time*1000:.1f} ms")

    if CUPY_AVAILABLE:
        # CuPy (GPU)
        start = time.time()
        gpu_array = cp.random.random(size)
        cp.cuda.Stream.null.synchronize()  # Wait for GPU
        gpu_time = time.time() - start
        print(f"   CuPy:  {gpu_time*1000:.1f} ms")
        print(f"   Speedup: {cpu_time/gpu_time:.1f}x")


def compare_matrix_operations():
    """เปรียบเทียบการคำนวณ matrix"""
    print("\n2. Matrix Multiplication:")

    n = 2000

    # NumPy
    a_cpu = np.random.random((n, n)).astype(np.float32)
    b_cpu = np.random.random((n, n)).astype(np.float32)

    start = time.time()
    c_cpu = np.dot(a_cpu, b_cpu)
    cpu_time = time.time() - start
    print(f"   NumPy ({n}x{n}): {cpu_time*1000:.1f} ms")

    if CUPY_AVAILABLE:
        # CuPy
        a_gpu = cp.asarray(a_cpu)
        b_gpu = cp.asarray(b_cpu)

        # Warm up
        cp.dot(a_gpu, b_gpu)
        cp.cuda.Stream.null.synchronize()

        start = time.time()
        c_gpu = cp.dot(a_gpu, b_gpu)
        cp.cuda.Stream.null.synchronize()
        gpu_time = time.time() - start

        print(f"   CuPy  ({n}x{n}): {gpu_time*1000:.1f} ms")
        print(f"   Speedup: {cpu_time/gpu_time:.1f}x")

        # Verify results
        c_cpu_from_gpu = cp.asnumpy(c_gpu)
        if np.allclose(c_cpu, c_cpu_from_gpu, rtol=1e-5):
            print("   Results verified!")


def compare_element_wise():
    """เปรียบเทียบ element-wise operations"""
    print("\n3. Element-wise Operations:")

    n = 10_000_000

    # NumPy
    x_cpu = np.random.random(n).astype(np.float32)

    start = time.time()
    result_cpu = np.sin(x_cpu) ** 2 + np.cos(x_cpu) ** 2
    cpu_time = time.time() - start
    print(f"   NumPy (sin²+cos²): {cpu_time*1000:.1f} ms")

    if CUPY_AVAILABLE:
        # CuPy
        x_gpu = cp.asarray(x_cpu)

        # Warm up
        cp.sin(x_gpu)
        cp.cuda.Stream.null.synchronize()

        start = time.time()
        result_gpu = cp.sin(x_gpu) ** 2 + cp.cos(x_gpu) ** 2
        cp.cuda.Stream.null.synchronize()
        gpu_time = time.time() - start

        print(f"   CuPy  (sin²+cos²): {gpu_time*1000:.1f} ms")
        print(f"   Speedup: {cpu_time/gpu_time:.1f}x")


def compare_reductions():
    """เปรียบเทียบ reduction operations"""
    print("\n4. Reduction Operations:")

    n = 50_000_000

    # NumPy
    x_cpu = np.random.random(n).astype(np.float32)

    start = time.time()
    sum_cpu = np.sum(x_cpu)
    mean_cpu = np.mean(x_cpu)
    std_cpu = np.std(x_cpu)
    cpu_time = time.time() - start
    print(f"   NumPy (sum, mean, std): {cpu_time*1000:.1f} ms")

    if CUPY_AVAILABLE:
        # CuPy
        x_gpu = cp.asarray(x_cpu)

        start = time.time()
        sum_gpu = cp.sum(x_gpu)
        mean_gpu = cp.mean(x_gpu)
        std_gpu = cp.std(x_gpu)
        cp.cuda.Stream.null.synchronize()
        gpu_time = time.time() - start

        print(f"   CuPy  (sum, mean, std): {gpu_time*1000:.1f} ms")
        print(f"   Speedup: {cpu_time/gpu_time:.1f}x")


def demonstrate_memory_transfer():
    """สาธิต memory transfer"""
    print("\n5. Memory Transfer:")

    n = 10_000_000
    x = np.random.random(n).astype(np.float32)
    size_mb = x.nbytes / 1e6

    if CUPY_AVAILABLE:
        # CPU to GPU
        start = time.time()
        x_gpu = cp.asarray(x)
        cp.cuda.Stream.null.synchronize()
        h2d_time = time.time() - start

        # GPU to CPU
        start = time.time()
        x_back = cp.asnumpy(x_gpu)
        d2h_time = time.time() - start

        print(f"   Data size: {size_mb:.1f} MB")
        print(f"   Host → Device: {h2d_time*1000:.1f} ms ({size_mb/h2d_time/1000:.1f} GB/s)")
        print(f"   Device → Host: {d2h_time*1000:.1f} ms ({size_mb/d2h_time/1000:.1f} GB/s)")
        print("\n   Tip: Minimize transfers for best performance!")


def demonstrate_cupy_numpy_compat():
    """สาธิต NumPy compatibility"""
    print("\n6. NumPy Compatibility:")

    if CUPY_AVAILABLE:
        # Same API!
        print("   Same API for NumPy and CuPy:")
        print("   ")
        print("   # NumPy                  # CuPy")
        print("   import numpy as np       import cupy as cp")
        print("   x = np.zeros((3,3))      x = cp.zeros((3,3))")
        print("   y = np.dot(x, x)         y = cp.dot(x, x)")
        print("   z = np.sum(x)            z = cp.sum(x)")

        # Write code that works with both
        print("\n   Write library-agnostic code:")
        print("   xp = cp.get_array_module(x)  # Returns numpy or cupy")
        print("   result = xp.sum(x)")


def main():
    print("=" * 60)
    print("   CuPy Basics - GPU Arrays")
    print("   Chapter 10: GPU Programming")
    print("=" * 60)

    if CUPY_AVAILABLE:
        device = cp.cuda.Device(0)
        print(f"\n   GPU: {cp.cuda.runtime.getDeviceProperties(0)['name'].decode()}")
        print(f"   Memory: {device.mem_info[1]/1e9:.1f} GB")

    compare_array_creation()
    compare_matrix_operations()
    compare_element_wise()
    compare_reductions()
    demonstrate_memory_transfer()
    demonstrate_cupy_numpy_compat()

    print("\n" + "=" * 60)
    print("   CuPy basics complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
