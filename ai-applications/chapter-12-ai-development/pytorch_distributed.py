#!/usr/bin/env python3
"""
PyTorch Distributed Training - การฝึกแบบกระจาย
Chapter 12: AI Development on HPC

Multi-GPU training with PyTorch DDP
"""

import os
import time
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.data.distributed import DistributedSampler


class SimpleModel(nn.Module):
    """Simple CNN for demonstration"""

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


def setup_distributed():
    """Initialize distributed training"""
    # Get environment variables from SLURM
    rank = int(os.environ.get('SLURM_PROCID', 0))
    world_size = int(os.environ.get('SLURM_NTASKS', 1))
    local_rank = int(os.environ.get('SLURM_LOCALID', 0))

    if not torch.cuda.is_available():
        raise RuntimeError("Distributed NCCL training requires CUDA, but CUDA is not available.")

    # Set CUDA device
    torch.cuda.set_device(local_rank)

    # Initialize process group
    dist.init_process_group(
        backend='nccl',
        init_method='env://',
        world_size=world_size,
        rank=rank
    )

    return rank, world_size, local_rank


def cleanup():
    """Clean up distributed training"""
    dist.destroy_process_group()


def create_dummy_data(batch_size: int, world_size: int):
    """Create dummy dataset for demonstration"""
    # Create random data
    n_samples = 1000 * world_size
    images = torch.randn(n_samples, 3, 32, 32)
    labels = torch.randint(0, 10, (n_samples,))

    dataset = TensorDataset(images, labels)
    return dataset


def train_epoch(model, dataloader, criterion, optimizer, device, epoch, rank):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    n_batches = 0

    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

        if batch_idx % 10 == 0 and rank == 0:
            print(f"   Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")

    return total_loss / n_batches


def main():
    parser = argparse.ArgumentParser(description='Distributed Training Demo')
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=0.001)
    args = parser.parse_args()

    world_size_env = int(os.environ.get('SLURM_NTASKS', 1))

    # A one-task Slurm smoke job should run as normal single-process PyTorch.
    if world_size_env > 1 and 'SLURM_PROCID' in os.environ:
        rank, world_size, local_rank = setup_distributed()
        device = torch.device(f'cuda:{local_rank}')
        distributed = True
    else:
        rank, world_size, local_rank = 0, 1, 0
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        distributed = False

    if rank == 0:
        print("=" * 60)
        print("   PyTorch Distributed Training")
        print("   Chapter 12: AI Development on HPC")
        print("=" * 60)
        print(f"\n   World size: {world_size}")
        print(f"   Device: {device}")
        print(f"   Distributed: {distributed}")

    # Create model
    model = SimpleModel(num_classes=10).to(device)

    if distributed:
        model = DDP(model, device_ids=[local_rank])

    # Create optimizer and loss
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    # Create dataset and dataloader
    dataset = create_dummy_data(args.batch_size, world_size)

    if distributed:
        sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    else:
        sampler = None

    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=2,
        pin_memory=device.type == "cuda"
    )

    # Training loop
    if rank == 0:
        print(f"\n   Training for {args.epochs} epochs...")
        start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        if distributed:
            sampler.set_epoch(epoch)

        avg_loss = train_epoch(model, dataloader, criterion, optimizer, device, epoch, rank)

        if rank == 0:
            print(f"   Epoch {epoch} complete, Avg Loss: {avg_loss:.4f}")

    if rank == 0:
        elapsed = time.time() - start_time
        print(f"\n   Training complete in {elapsed:.2f}s")
        print("=" * 60)

    if distributed:
        cleanup()


if __name__ == "__main__":
    main()
