"""Tests for MerkleTree implementation."""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
import json

from merkle.tree import MerkleTree
from merkle.exceptions import EmptyTreeError


class TestMerkleTreeBasic:
    """Basic MerkleTree functionality tests."""
    
    def test_empty_tree(self):
        """Test empty tree initialization."""
        tree = MerkleTree()
        assert tree.root is None
        assert len(tree) == 0
        assert str(tree) == "MerkleTree(empty)"
        
        with pytest.raises(EmptyTreeError):
            tree.get_root_hash()
    
    def test_current_project_tree(self):
        """Test building tree from current mini-cursor-cli project."""
        # Get project root (assuming test runs from project root)
        project_root = Path(__file__).parent.parent
        
        tree = MerkleTree(str(project_root))
        
        # Basic assertions
        assert tree.root is not None
        assert tree.get_root_hash() is not None
        assert len(tree.get_root_hash()) == 64  # SHA-256 hex length
        assert len(tree) > 0  # Should have some files
        
        # Check that it found our project files
        assert "merkle" in tree.root.children
        assert "tests" in tree.root.children
        
        # Verify merkle directory structure
        merkle_node = tree.root.children["merkle"]
        assert not merkle_node.is_file  # Directory
        assert "tree.py" in merkle_node.children
        assert "node.py" in merkle_node.children
        
        # Verify files are marked correctly
        tree_py = merkle_node.children["tree.py"]
        assert tree_py.is_file
        assert tree_py.hash is not None
        
        print(f"✅ Project tree: {tree}")
        print(f"📁 Root hash: {tree.get_root_hash()[:16]}...")


class TestMerkleTreeTempDirectory:
    """Tests with temporary directories for controlled scenarios."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test project structure
        project_structure = {
            "src/main.py": "def main():\n    print('Hello, World!')\n",
            "src/utils.py": "def helper():\n    return 42\n",
            "tests/test_main.py": "def test_main():\n    assert True\n",
            "README.md": "# Test Project\n\nThis is a test.\n",
            "requirements.txt": "pytest>=7.0.0\n",
            "docs/api.md": "# API Documentation\n",
            ".env": "SECRET_KEY=secret123",  # Should be ignored
            ".git/config": "[core]\n",      # Should be ignored
        }
        
        for file_path, content in project_structure.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_temp_directory_tree(self, temp_project):
        """Test building tree from temporary directory."""
        tree = MerkleTree(temp_project)
        
        # Check basic structure
        assert tree.root is not None
        assert len(tree) == 6  # Should ignore .env and .git files
        
        # Verify directory structure
        assert "src" in tree.root.children
        assert "tests" in tree.root.children
        assert "docs" in tree.root.children
        assert "README.md" in tree.root.children
        assert "requirements.txt" in tree.root.children
        
        # Verify ignored files are not present
        assert ".env" not in tree.root.children
        assert ".git" not in tree.root.children
        
        # Check file content hashes are different
        main_py = tree.root.children["src"].children["main.py"]
        utils_py = tree.root.children["src"].children["utils.py"]
        assert main_py.hash != utils_py.hash
        
        print(f"✅ Temp tree: {tree}")
    
    def test_file_modification_detection(self, temp_project):
        """Test that file modifications are detected correctly."""
        # Build initial tree
        tree1 = MerkleTree(temp_project)
        initial_hash = tree1.get_root_hash()
        
        # Modify a file
        main_py_path = os.path.join(temp_project, "src", "main.py")
        with open(main_py_path, 'a') as f:
            f.write("\n# Modified file")
        
        # Build new tree
        tree2 = MerkleTree(temp_project)
        modified_hash = tree2.get_root_hash()
        
        # Hashes should be different
        assert initial_hash != modified_hash
        
        # Find differences
        changed_files = tree1.find_differences(tree2)
        assert len(changed_files) == 1
        assert changed_files[0].endswith("src/main.py")
        
        print(f"✅ Detected change: {changed_files[0]}")
    
    def test_file_addition_deletion(self, temp_project):
        """Test detection of added and deleted files."""
        # Build initial tree
        tree1 = MerkleTree(temp_project)
        
        # Add a new file
        new_file = os.path.join(temp_project, "src", "new_module.py")
        with open(new_file, 'w') as f:
            f.write("def new_function():\n    pass\n")
        
        # Delete an existing file
        old_file = os.path.join(temp_project, "tests", "test_main.py")
        os.remove(old_file)
        
        # Build new tree
        tree2 = MerkleTree(temp_project)
        
        # Find differences
        changed_files = tree1.find_differences(tree2)
        changed_paths = [os.path.basename(path) for path in changed_files]
        
        assert "new_module.py" in changed_paths
        assert "test_main.py" in changed_paths
        assert len(changed_files) == 2
        
        print(f"✅ Added/Deleted files: {changed_files}")


class TestMerkleTreeSerialization:
    """Test serialization and deserialization functionality."""
    
    @pytest.fixture
    def simple_tree(self):
        """Create a simple tree for serialization tests."""
        temp_dir = tempfile.mkdtemp()
        
        # Simple structure
        files = {
            "file1.txt": "content1",
            "dir1/file2.txt": "content2",
            "dir1/subdir/file3.txt": "content3"
        }
        
        for file_path, content in files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        tree = MerkleTree(temp_dir)
        yield tree, temp_dir
        
        shutil.rmtree(temp_dir)
    
    def test_to_dict_serialization(self, simple_tree):
        """Test tree serialization to dictionary."""
        tree, _ = simple_tree
        
        tree_dict = tree.to_dict()
        
        # Check basic structure
        assert "root" in tree_dict
        assert "root_path" in tree_dict
        assert tree_dict["root"]["name"] == os.path.basename(tree.root_path)
        assert not tree_dict["root"]["is_file"]
        assert "children" in tree_dict["root"]
        
        # Check serialization preserves structure
        children = tree_dict["root"]["children"]
        assert "file1.txt" in children
        assert "dir1" in children
        assert children["file1.txt"]["is_file"] is True
        assert children["dir1"]["is_file"] is False
        
        print(f"✅ Serialized tree structure: {list(children.keys())}")
    
    def test_from_dict_deserialization(self, simple_tree):
        """Test tree reconstruction from dictionary."""
        original_tree, _ = simple_tree
        
        # Serialize
        tree_dict = original_tree.to_dict()
        
        # Deserialize
        reconstructed_tree = MerkleTree.from_dict(tree_dict)
        
        # Compare trees
        assert original_tree.get_root_hash() == reconstructed_tree.get_root_hash()
        assert len(original_tree) == len(reconstructed_tree)
        
        # Should find no differences
        differences = original_tree.find_differences(reconstructed_tree)
        assert len(differences) == 0
        
        print(f"✅ Reconstructed tree matches original")
    
    def test_json_roundtrip(self, simple_tree):
        """Test complete JSON serialization roundtrip."""
        original_tree, _ = simple_tree
        
        # Serialize to JSON string
        tree_dict = original_tree.to_dict()
        json_str = json.dumps(tree_dict)
        
        # Deserialize from JSON string
        reconstructed_dict = json.loads(json_str)
        reconstructed_tree = MerkleTree.from_dict(reconstructed_dict)
        
        # Verify integrity
        assert original_tree.get_root_hash() == reconstructed_tree.get_root_hash()
        
        print(f"✅ JSON roundtrip successful")


class TestMerkleTreeComparison:
    """Test tree comparison algorithms."""
    
    @pytest.fixture
    def comparison_trees(self):
        """Create two similar trees for comparison testing."""
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()
        
        # Create identical initial structure
        files = {
            "common.txt": "same content",
            "dir1/shared.py": "def shared(): pass",
            "dir2/data.json": '{"key": "value"}',
        }
        
        for temp_dir in [temp_dir1, temp_dir2]:
            for file_path, content in files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
        
        tree1 = MerkleTree(temp_dir1)
        tree2 = MerkleTree(temp_dir2)
        
        yield tree1, tree2, temp_dir1, temp_dir2
        
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)
    
    def test_identical_trees(self, comparison_trees):
        """Test comparison of identical trees."""
        tree1, tree2, _, _ = comparison_trees
        
        # Identical trees should have same hash
        assert tree1.get_root_hash() == tree2.get_root_hash()
        
        # No differences should be found
        differences = tree1.find_differences(tree2)
        assert len(differences) == 0
        
        print(f"✅ Identical trees correctly identified")
    
    def test_tree_differences(self, comparison_trees):
        """Test detection of various types of differences."""
        tree1, tree2, temp_dir1, temp_dir2 = comparison_trees
        
        # Modify file in tree2
        modified_file = os.path.join(temp_dir2, "common.txt")
        with open(modified_file, 'w') as f:
            f.write("different content")
        
        # Add file to tree2
        new_file = os.path.join(temp_dir2, "new_file.txt")
        with open(new_file, 'w') as f:
            f.write("new content")
        
        # Remove file from tree2
        removed_file = os.path.join(temp_dir2, "dir2", "data.json")
        os.remove(removed_file)
        
        # Rebuild tree2
        tree2_modified = MerkleTree(temp_dir2)
        
        # Find differences
        differences = tree1.find_differences(tree2_modified)
        
        # Should detect all changes
        assert len(differences) >= 3  # Modified, added, removed
        
        basenames = [os.path.basename(path) for path in differences]
        assert "common.txt" in basenames      # Modified
        assert "new_file.txt" in basenames   # Added
        assert "data.json" in basenames      # Removed
        
        print(f"✅ Detected {len(differences)} differences: {basenames}")


class TestMerkleTreeEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_path(self):
        """Test handling of nonexistent paths."""
        with pytest.raises(FileNotFoundError):
            MerkleTree("/this/path/does/not/exist")
    
    def test_empty_directory(self):
        """Test handling of empty directories."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            tree = MerkleTree(temp_dir)
            assert tree.root is not None
            assert len(tree) == 0
            assert len(tree.root.children) == 0
        finally:
            shutil.rmtree(temp_dir)
    
    def test_single_file(self):
        """Test tree with single file."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create single file
            test_file = os.path.join(temp_dir, "single.txt")
            with open(test_file, 'w') as f:
                f.write("single file content")
            
            tree = MerkleTree(temp_dir)
            assert len(tree) == 1
            assert "single.txt" in tree.root.children
            assert tree.root.children["single.txt"].is_file
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_deeply_nested_structure(self):
        """Test deeply nested directory structure."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create deeply nested structure
            deep_path = os.path.join(temp_dir, "a", "b", "c", "d", "e")
            os.makedirs(deep_path)
            
            deep_file = os.path.join(deep_path, "deep.txt")
            with open(deep_file, 'w') as f:
                f.write("deep content")
            
            tree = MerkleTree(temp_dir)
            assert len(tree) == 1
            
            # Navigate to deep file
            current = tree.root
            for dir_name in ["a", "b", "c", "d", "e"]:
                assert dir_name in current.children
                current = current.children[dir_name]
                assert not current.is_file
            
            assert "deep.txt" in current.children
            assert current.children["deep.txt"].is_file
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_merkle_tree.py -v
    pytest.main([__file__, "-v", "--tb=short"]) 