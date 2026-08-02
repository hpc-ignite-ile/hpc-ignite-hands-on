#!/usr/bin/env python3
"""
GPU Information - ข้อมูล GPU
Chapter 10: GPU Programming

ตรวจสอบ GPU ที่ใช้ได้และแสดงข้อมูล
"""

import os
import subprocess


def check_nvidia_smi():
    """ตรวจสอบ GPU ด้วย nvidia-smi"""
    print("\n1. NVIDIA SMI:")

    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,driver_version,compute_mode',
             '--format=csv,noheader'],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"   Found {len(lines)} GPU(s):")
            for i, line in enumerate(lines):
                parts = line.split(', ')
                print(f"\n   GPU {i}:")
                print(f"      Name: {parts[0]}")
                print(f"      Memory: {parts[1]}")
                print(f"      Driver: {parts[2]}")
                print(f"      Compute Mode: {parts[3]}")
            return True
        else:
            print("   nvidia-smi failed")
            return False

    except FileNotFoundError:
        print("   nvidia-smi not found (no NVIDIA driver)")
        return False
    except Exception as e:
        print(f"   Error: {e}")
        return False


def check_cuda_env():
    """ตรวจสอบ CUDA Environment"""
    print("\n2. CUDA Environment:")

    cuda_vars = ['CUDA_HOME', 'CUDA_PATH', 'CUDA_VERSION', 'CUDA_VISIBLE_DEVICES']
    found = False

    for var in cuda_vars:
        value = os.environ.get(var)
        if value:
            print(f"   {var}: {value}")
            found = True

    if not found:
        print("   No CUDA environment variables set")
        print("   On LANTA, source slurm/module-loads/pytorch-shared.sh for the shared GPU smoke environment")


def check_pytorch():
    """ตรวจสอบ PyTorch CUDA"""
    print("\n3. PyTorch CUDA:")

    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   cuDNN version: {torch.backends.cudnn.version()}")
            print(f"   Device count: {torch.cuda.device_count()}")

            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"\n   Device {i}: {props.name}")
                print(f"      Compute capability: {props.major}.{props.minor}")
                print(f"      Total memory: {props.total_memory / 1e9:.1f} GB")
                print(f"      Multi-processors: {props.multi_processor_count}")
        else:
            print("   CUDA not available in PyTorch")

    except ImportError:
        print("   PyTorch not installed")


def check_cupy():
    """ตรวจสอบ CuPy"""
    print("\n4. CuPy:")

    try:
        import cupy as cp
        print(f"   CuPy version: {cp.__version__}")

        device = cp.cuda.Device(0)
        print(f"   Device: {device.compute_capability}")
        print(f"   Memory: {device.mem_info[1] / 1e9:.1f} GB total")
        print(f"   Free: {device.mem_info[0] / 1e9:.1f} GB")

    except ImportError:
        print("   CuPy not installed")
        print("   Use CuPy only from a prebuilt project environment for live training")
    except Exception as e:
        print(f"   CuPy error: {e}")


def check_numba():
    """ตรวจสอบ Numba CUDA"""
    print("\n5. Numba CUDA:")

    try:
        from numba import cuda
        print(f"   Numba CUDA available: {cuda.is_available()}")

        if cuda.is_available():
            device = cuda.get_current_device()
            print(f"   Device: {device.name}")
            print(f"   Compute capability: {device.compute_capability}")

    except ImportError:
        print("   Numba not installed")
    except Exception as e:
        print(f"   Numba error: {e}")


def main():
    print("=" * 60)
    print("   GPU Information")
    print("   Chapter 10: GPU Programming")
    print("=" * 60)

    has_gpu = check_nvidia_smi()
    check_cuda_env()
    check_pytorch()
    check_cupy()
    check_numba()

    print("\n" + "=" * 60)
    if has_gpu:
        print("   GPU detected! Ready for CUDA programming.")
    else:
        print("   No GPU detected. Running on CPU only.")
        print("\n   On LANTA, request GPU node:")
        print("   srun -p gpu-devel -N 1 --gpus=1 --pty bash")
    print("=" * 60)


if __name__ == "__main__":
    main()
