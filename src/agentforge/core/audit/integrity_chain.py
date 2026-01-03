# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: integrity-chain
# @test_path: tests/unit/audit/test_integrity_chain.py

"""
Integrity Chain
===============

Provides tamper-evident logging through cryptographic hash chains.

Each transaction includes:
- Content hash: SHA-256 of transaction content
- Previous hash: Hash of the previous transaction in chain

This creates an immutable chain where any modification to historical
transactions would break the chain verification.

Verification:
1. Compute hash of each transaction content
2. Verify it matches stored content_hash
3. Verify previous_hash matches content_hash of prior transaction
4. Chain is valid if all links verify
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import yaml


def compute_hash(data: dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of data dictionary.

    Normalizes data for consistent hashing:
    - Sorts keys
    - Converts to JSON
    - Uses UTF-8 encoding

    Args:
        data: Dictionary to hash

    Returns:
        Hex-encoded SHA-256 hash (64 characters)
    """
    # Remove hash fields to avoid circular reference
    data_copy = {k: v for k, v in data.items() if k not in ("content_hash", "previous_hash")}

    # Normalize to JSON for consistent hashing
    content = json.dumps(data_copy, sort_keys=True, default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class ChainBlock:
    """A single block in the integrity chain."""

    block_id: str  # Transaction or event ID
    content_hash: str  # SHA-256 of content
    previous_hash: str | None  # Hash of previous block
    timestamp: str  # When block was created

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "block_id": self.block_id,
            "content_hash": self.content_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
        }


@dataclass
class ChainVerificationResult:
    """Result of chain verification."""

    valid: bool
    total_blocks: int
    verified_blocks: int
    first_invalid_block: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "valid": self.valid,
            "total_blocks": self.total_blocks,
            "verified_blocks": self.verified_blocks,
            "first_invalid_block": self.first_invalid_block,
            "error": self.error,
        }


class IntegrityChain:
    """
    Manages tamper-evident hash chain for a thread.

    The chain is stored in two formats:
    1. chain.sig: Compact format (block_id:hash per line)
    2. chain.yaml: Full format with all metadata

    Verification checks:
    - Each block's content_hash matches computed hash
    - Each block's previous_hash matches prior block's content_hash
    """

    def __init__(self, thread_dir: Path):
        """
        Initialize integrity chain for a thread.

        Args:
            thread_dir: Thread directory containing chain files
        """
        self.thread_dir = Path(thread_dir)
        self.chain_sig_path = self.thread_dir / "chain.sig"
        self.chain_yaml_path = self.thread_dir / "chain.yaml"

        # Ensure directory exists
        self.thread_dir.mkdir(parents=True, exist_ok=True)

    def append(self, block_id: str, content: dict[str, Any]) -> ChainBlock:
        """
        Append a new block to the chain.

        Args:
            block_id: Unique identifier for this block
            content: Content to hash and chain

        Returns:
            Created ChainBlock
        """
        # Compute content hash
        content_hash = compute_hash(content)

        # Get previous hash
        previous_hash = self.get_last_hash()

        # Create block
        block = ChainBlock(
            block_id=block_id,
            content_hash=content_hash,
            previous_hash=previous_hash,
            timestamp=datetime.now(UTC).isoformat(),
        )

        # Append to chain files
        self._append_to_sig(block)
        self._append_to_yaml(block)

        return block

    def get_last_hash(self) -> str | None:
        """Get hash of last block in chain."""
        if not self.chain_sig_path.exists():
            return None

        content = self.chain_sig_path.read_text(encoding="utf-8").strip()
        if not content:
            return None

        lines = content.split("\n")
        last_line = lines[-1]

        # Format is "block_id:hash"
        parts = last_line.split(":")
        if len(parts) >= 2:
            return parts[1].strip()

        return None

    def get_chain(self) -> list[ChainBlock]:
        """Load full chain from YAML file."""
        if not self.chain_yaml_path.exists():
            return []

        data = yaml.safe_load(self.chain_yaml_path.read_text(encoding="utf-8"))
        if not data or "blocks" not in data:
            return []

        return [
            ChainBlock(
                block_id=b["block_id"],
                content_hash=b["content_hash"],
                previous_hash=b.get("previous_hash"),
                timestamp=b["timestamp"],
            )
            for b in data["blocks"]
        ]

    def verify(self, content_loader: Callable[[str], dict[str, Any] | None] | None = None) -> ChainVerificationResult:
        """
        Verify the integrity of the chain.

        Args:
            content_loader: Optional function to load content for a block_id.
                           If provided, also verifies content hashes.
                           Signature: (block_id: str) -> dict[str, Any] | None

        Returns:
            ChainVerificationResult with verification status
        """
        chain = self.get_chain()
        if not chain:
            return ChainVerificationResult(
                valid=True,
                total_blocks=0,
                verified_blocks=0,
            )

        verified = 0
        previous_hash = None

        for block in chain:
            # Verify chain link
            if block.previous_hash != previous_hash:
                return ChainVerificationResult(
                    valid=False,
                    total_blocks=len(chain),
                    verified_blocks=verified,
                    first_invalid_block=block.block_id,
                    error=f"Chain broken at {block.block_id}: expected previous_hash "
                    f"{previous_hash}, got {block.previous_hash}",
                )

            # Verify content hash if loader provided
            if content_loader:
                content = content_loader(block.block_id)
                if content is not None:
                    computed = compute_hash(content)
                    if computed != block.content_hash:
                        return ChainVerificationResult(
                            valid=False,
                            total_blocks=len(chain),
                            verified_blocks=verified,
                            first_invalid_block=block.block_id,
                            error=f"Content hash mismatch at {block.block_id}: "
                            f"expected {block.content_hash}, computed {computed}",
                        )

            verified += 1
            previous_hash = block.content_hash

        return ChainVerificationResult(
            valid=True,
            total_blocks=len(chain),
            verified_blocks=verified,
        )

    def get_block(self, block_id: str) -> ChainBlock | None:
        """Get a specific block by ID."""
        for block in self.get_chain():
            if block.block_id == block_id:
                return block
        return None

    def get_proof(self, block_id: str) -> dict[str, Any] | None:
        """
        Generate a proof of inclusion for a block.

        The proof contains:
        - The block itself
        - All subsequent blocks (to verify the chain continues)
        - Final hash

        This proves the block was part of the chain at a point in time.
        """
        chain = self.get_chain()
        block_found = False
        proof_blocks = []

        for block in chain:
            if block.block_id == block_id:
                block_found = True

            if block_found:
                proof_blocks.append(block.to_dict())

        if not block_found:
            return None

        return {
            "block_id": block_id,
            "proof_type": "inclusion",
            "proof_blocks": proof_blocks,
            "final_hash": chain[-1].content_hash if chain else None,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _append_to_sig(self, block: ChainBlock) -> None:
        """Append block to .sig file (compact format)."""
        with self.chain_sig_path.open("a", encoding="utf-8") as f:
            f.write(f"{block.block_id}:{block.content_hash}\n")

    def _append_to_yaml(self, block: ChainBlock) -> None:
        """Append block to .yaml file (full format)."""
        # Load existing or create new
        if self.chain_yaml_path.exists():
            data = yaml.safe_load(self.chain_yaml_path.read_text(encoding="utf-8"))
        else:
            data = {"blocks": [], "created_at": datetime.now(UTC).isoformat()}

        data["blocks"].append(block.to_dict())
        data["last_updated"] = datetime.now(UTC).isoformat()
        data["block_count"] = len(data["blocks"])

        self.chain_yaml_path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )


def verify_thread_integrity(
    thread_dir: Path,
    transactions_dir: Path | None = None,
) -> ChainVerificationResult:
    """
    Verify integrity of a thread's audit trail.

    Args:
        thread_dir: Thread directory
        transactions_dir: Optional transactions directory (default: thread_dir/transactions)

    Returns:
        Verification result
    """
    chain = IntegrityChain(thread_dir)

    if transactions_dir is None:
        transactions_dir = thread_dir / "transactions"

    def load_transaction(block_id: str) -> dict[str, Any] | None:
        tx_path = transactions_dir / f"{block_id}.yaml"
        if tx_path.exists():
            data = yaml.safe_load(tx_path.read_text(encoding="utf-8"))
            return data
        return None

    return chain.verify(content_loader=load_transaction)
