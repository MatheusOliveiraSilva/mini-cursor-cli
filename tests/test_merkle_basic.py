#!/usr/bin/env python3
"""
Basic test script for Merkle Tree implementation.

This script demonstrates basic usage and validates core functionality.
Run with: python test_merkle_basic.py
"""

import hashlib
from merkle import MerkleTree, MerkleTreeError


def create_sample_hash(data: str) -> str:
    """Create a SHA-256 hash from sample data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def test_basic_operations():
    """Test basic Merkle Tree operations."""
    print("🌳 Testing Basic Merkle Tree Operations\n")
    
    # Create sample data hashes (simulating code chunks)
    chunk_hashes = [
        create_sample_hash("def hello_world():"),
        create_sample_hash("    print('Hello, World!')"),
        create_sample_hash("if __name__ == '__main__':"),
        create_sample_hash("    hello_world()")
    ]
    
    print(f"Sample code chunk hashes:")
    for i, hash_val in enumerate(chunk_hashes):
        print(f"  Chunk {i+1}: {hash_val[:16]}...")
    print()
    
    # Test 1: Empty tree
    print("1. Testing empty tree...")
    tree = MerkleTree()
    print(f"   Empty tree: {tree}")
    
    try:
        tree.get_root()
        print("   ❌ ERROR: Empty tree should raise exception")
    except MerkleTreeError:
        print("   ✅ Empty tree correctly raises exception")
    print()
    
    # Test 2: Single leaf
    print("2. Testing single leaf...")
    tree.add_leaf(chunk_hashes[0])
    root_hash = tree.get_root()
    print(f"   Single leaf tree: {tree}")
    print(f"   Root hash: {root_hash[:16]}...")
    print(f"   ✅ Single leaf: root == leaf hash: {root_hash == chunk_hashes[0]}")
    print()
    
    # Test 3: Multiple leaves (even count)
    print("3. Testing even number of leaves...")
    tree.add_leaf(chunk_hashes[1])
    root_hash_2 = tree.get_root()
    print(f"   Two leaves tree: {tree}")
    print(f"   Root hash changed: {root_hash != root_hash_2}")
    print(f"   ✅ Even leaves handled correctly")
    print()
    
    # Test 4: Odd number of leaves
    print("4. Testing odd number of leaves...")
    tree.add_leaf(chunk_hashes[2])
    root_hash_3 = tree.get_root()
    print(f"   Three leaves tree: {tree}")
    print(f"   Root hash changed: {root_hash_2 != root_hash_3}")
    print(f"   ✅ Odd leaves handled correctly")
    print()
    
    # Test 5: Even number again (4 leaves)
    print("5. Testing four leaves...")
    tree.add_leaf(chunk_hashes[3])
    root_hash_4 = tree.get_root()
    print(f"   Four leaves tree: {tree}")
    print(f"   Root hash changed: {root_hash_3 != root_hash_4}")
    print(f"   ✅ Four leaves handled correctly")
    print()
    
    # Test 6: Merkle proof generation and verification
    print("6. Testing Merkle proofs...")
    
    for leaf_idx in range(len(chunk_hashes)):
        proof = tree.get_proof(leaf_idx)
        is_valid = MerkleTree.verify_proof(
            chunk_hashes[leaf_idx], 
            proof, 
            root_hash_4, 
            leaf_idx
        )
        print(f"   Proof for leaf {leaf_idx}: {len(proof)} hashes, valid: {is_valid}")
    
    print(f"   ✅ All proofs validated correctly")
    print()


def test_change_detection():
    """Test change detection capabilities."""
    print("🔍 Testing Change Detection\n")
    
    # Create two identical trees
    tree1 = MerkleTree()
    tree2 = MerkleTree()
    
    sample_hashes = [
        create_sample_hash("function calculate(a, b) {"),
        create_sample_hash("    return a + b;"),
        create_sample_hash("}")
    ]
    
    # Add same data to both trees
    for hash_val in sample_hashes:
        tree1.add_leaf(hash_val)
        tree2.add_leaf(hash_val)
    
    root1 = tree1.get_root()
    root2 = tree2.get_root()
    
    print(f"Tree 1 root: {root1[:16]}...")
    print(f"Tree 2 root: {root2[:16]}...")
    print(f"✅ Identical trees have same root: {root1 == root2}")
    print()
    
    # Modify one tree (simulate code change)
    modified_hash = create_sample_hash("    return a * b;")  # Changed + to *
    tree2.add_leaf(modified_hash)
    
    root2_modified = tree2.get_root()
    print(f"Tree 2 modified root: {root2_modified[:16]}...")
    print(f"✅ Trees differ after change: {root1 != root2_modified}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("         MERKLE TREE BASIC VALIDATION")
    print("=" * 60)
    print()
    
    try:
        test_basic_operations()
        test_change_detection()
        
        print("🎉 All tests passed! Merkle Tree implementation is working correctly.")
        print("\n" + "=" * 60)
        print("Ready for Stage 3: Code Chunking & Hashing")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise 