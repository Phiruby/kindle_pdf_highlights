import os
from enum import Enum
from datetime import datetime

class NodeType(Enum):
    FILE = "file"
    DIRECTORY = "directory"

class Node:
    def __init__(self, name: str, type: NodeType, last_updated: str, children = []):
        self.name = name
        self.children = children
        # convert from string to datetime object
        self.last_updated = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self):
        return f"Node({self.name}, {self.children})"