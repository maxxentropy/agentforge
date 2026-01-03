# @spec_file: .agentforge/specs/core-audit-v1.yaml
# @spec_id: core-audit-v1
# @component_id: integrity-chain-tests

"""Tests for IntegrityChain - tamper-evident logging."""

import yaml
import pytest

from agentforge.core.audit.integrity_chain import (
    ChainBlock,
    IntegrityChain,
    compute_hash,
    verify_thread_integrity,
)


class TestComputeHash:
    """Tests for hash computation."""

    def test_deterministic_hash(self):
        """Same data should produce same hash."""
        data = {"key": "value", "number": 42}

        hash1 = compute_hash(data)
        hash2 = compute_hash(data)

        assert hash1 == hash2, "Expected hash1 to equal hash2"

    def test_different_data_different_hash(self):
        """Different data should produce different hashes."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        assert hash1 != hash2, "Expected hash1 to not equal hash2"

    def test_key_order_independent(self):
        """Hash should be independent of key order."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        assert compute_hash(data1) == compute_hash(data2), "Expected compute_hash(data1) to equal compute_hash(data2)"

    def test_excludes_hash_fields(self):
        """Hash fields should not affect computed hash."""
        data = {"key": "value", "content_hash": "abc", "previous_hash": "xyz"}

        hash_with = compute_hash(data)
        data_without = {"key": "value"}
        hash_without = compute_hash(data_without)

        assert hash_with == hash_without, "Expected hash_with to equal hash_without"

    def test_hash_length(self):
        """Hash should be 64 hex characters (SHA-256)."""
        data = {"test": "data"}
        h = compute_hash(data)

        assert len(h) == 64, "Expected len(h) to equal 64"
        assert all(c in "0123456789abcdef" for c in h), "Expected all() to be truthy"


class TestIntegrityChain:
    """Tests for IntegrityChain."""

    def test_append_first_block(self, tmp_path):
        """First block should have no previous hash."""
        chain = IntegrityChain(tmp_path)

        block = chain.append("TX-0001", {"data": "first"})

        assert block.block_id == "TX-0001", "Expected block.block_id to equal 'TX-0001'"
        assert block.previous_hash is None, "Expected block.previous_hash is None"
        assert block.content_hash is not None, "Expected block.content_hash is not None"

    def test_append_links_to_previous(self, tmp_path):
        """Subsequent blocks should link to previous hash."""
        chain = IntegrityChain(tmp_path)

        b1 = chain.append("TX-0001", {"data": "first"})
        b2 = chain.append("TX-0002", {"data": "second"})

        assert b2.previous_hash == b1.content_hash, "Expected b2.previous_hash to equal b1.content_hash"

    def test_get_chain(self, tmp_path):
        """Retrieve full chain."""
        chain = IntegrityChain(tmp_path)

        chain.append("TX-0001", {"data": "first"})
        chain.append("TX-0002", {"data": "second"})
        chain.append("TX-0003", {"data": "third"})

        blocks = chain.get_chain()

        assert len(blocks) == 3, "Expected len(blocks) to equal 3"
        assert blocks[0].block_id == "TX-0001", "Expected blocks[0].block_id to equal 'TX-0001'"
        assert blocks[1].block_id == "TX-0002", "Expected blocks[1].block_id to equal 'TX-0002'"
        assert blocks[2].block_id == "TX-0003", "Expected blocks[2].block_id to equal 'TX-0003'"

    def test_verify_valid_chain(self, tmp_path):
        """Valid chain should pass verification."""
        chain = IntegrityChain(tmp_path)

        chain.append("TX-0001", {"data": "first"})
        chain.append("TX-0002", {"data": "second"})

        result = chain.verify()

        assert result.valid is True, "Expected result.valid is True"
        assert result.total_blocks == 2, "Expected result.total_blocks to equal 2"
        assert result.verified_blocks == 2, "Expected result.verified_blocks to equal 2"

    def test_verify_with_content_loader(self, tmp_path):
        """Verification with content loader should check hashes."""
        chain = IntegrityChain(tmp_path)

        # Store original data
        data1 = {"data": "first"}
        data2 = {"data": "second"}
        chain.append("TX-0001", data1)
        chain.append("TX-0002", data2)

        # Content loader returns original data
        content_store = {"TX-0001": data1, "TX-0002": data2}

        result = chain.verify(content_loader=lambda bid: content_store.get(bid))

        assert result.valid is True, "Expected result.valid is True"

    def test_verify_detects_tampered_content(self, tmp_path):
        """Verification should detect tampered content."""
        chain = IntegrityChain(tmp_path)

        original_data = {"data": "original"}
        chain.append("TX-0001", original_data)

        # Simulate tampering - content loader returns different data
        tampered_data = {"data": "tampered"}

        result = chain.verify(content_loader=lambda bid: tampered_data)

        assert result.valid is False, "Expected result.valid is False"
        assert "Content hash mismatch" in result.error, "Expected 'Content hash mismatch' in result.error"

    def test_verify_detects_broken_chain(self, tmp_path):
        """Verification should detect broken chain link."""
        chain = IntegrityChain(tmp_path)

        chain.append("TX-0001", {"data": "first"})
        chain.append("TX-0002", {"data": "second"})

        # Manually corrupt the chain file
        chain_yaml = tmp_path / "chain.yaml"
        data = yaml.safe_load(chain_yaml.read_text())
        # Corrupt the previous_hash of second block
        data["blocks"][1]["previous_hash"] = "invalid_hash"
        chain_yaml.write_text(yaml.dump(data))

        result = chain.verify()

        assert result.valid is False, "Expected result.valid is False"
        assert "Chain broken" in result.error, "Expected 'Chain broken' in result.error"
        assert result.first_invalid_block == "TX-0002", "Expected result.first_invalid_block to equal 'TX-0002'"

    def test_get_block(self, tmp_path):
        """Retrieve specific block by ID."""
        chain = IntegrityChain(tmp_path)

        chain.append("TX-0001", {"data": "first"})
        chain.append("TX-0002", {"data": "second"})

        block = chain.get_block("TX-0002")

        assert block is not None, "Expected block is not None"
        assert block.block_id == "TX-0002", "Expected block.block_id to equal 'TX-0002'"

    def test_get_nonexistent_block(self, tmp_path):
        """Non-existent block returns None."""
        chain = IntegrityChain(tmp_path)

        block = chain.get_block("TX-9999")

        assert block is None, "Expected block is None"

    def test_get_proof(self, tmp_path):
        """Generate proof of inclusion for a block."""
        chain = IntegrityChain(tmp_path)

        chain.append("TX-0001", {"data": "first"})
        chain.append("TX-0002", {"data": "second"})
        chain.append("TX-0003", {"data": "third"})

        proof = chain.get_proof("TX-0002")

        assert proof is not None, "Expected proof is not None"
        assert proof["block_id"] == "TX-0002", "Expected proof['block_id'] to equal 'TX-0002'"
        assert len(proof["proof_blocks"]) == 2, "Expected len(proof['proof_blocks']) to equal 2"# TX-0002 and TX-0003
        assert proof["final_hash"] is not None, "Expected proof['final_hash'] is not None"

    def test_empty_chain_is_valid(self, tmp_path):
        """Empty chain should be valid."""
        chain = IntegrityChain(tmp_path)

        result = chain.verify()

        assert result.valid is True, "Expected result.valid is True"
        assert result.total_blocks == 0, "Expected result.total_blocks to equal 0"

    def test_chain_persistence(self, tmp_path):
        """Chain should persist across instances."""
        # First instance
        chain1 = IntegrityChain(tmp_path)
        chain1.append("TX-0001", {"data": "first"})

        # Second instance
        chain2 = IntegrityChain(tmp_path)
        b2 = chain2.append("TX-0002", {"data": "second"})

        # Should link to first
        assert b2.previous_hash is not None, "Expected b2.previous_hash is not None"

        # Full chain should have both
        blocks = chain2.get_chain()
        assert len(blocks) == 2, "Expected len(blocks) to equal 2"


class TestVerifyThreadIntegrity:
    """Tests for verify_thread_integrity helper."""

    def test_verify_thread_with_transactions(self, tmp_path):
        """Verify thread integrity using transaction files."""
        from agentforge.core.audit.transaction_logger import TransactionLogger

        logger = TransactionLogger(tmp_path, "test-thread")
        logger.log_llm_call(request={}, response="First")
        logger.log_llm_call(request={}, response="Second")

        thread_dir = tmp_path / ".agentforge" / "audit" / "threads" / "test-thread"
        result = verify_thread_integrity(thread_dir)

        assert result.valid is True, "Expected result.valid is True"
        assert result.total_blocks == 2, "Expected result.total_blocks to equal 2"
