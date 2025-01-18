import os
from enum import Enum
from datetime import datetime

class NodeType(Enum):
    FILE = "file"
    DIRECTORY = "directory"

class Node:
    def __init__(self, name: str, type: NodeType, last_updated: str = "", children = []):
        self.name = name
        self.children = children
        self.type = type 

        self.last_updated = "" 
        # oonly add this info if a file
        if NodeType.FILE == type:      
            # convert from string to datetime object
            self.last_updated = datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%SZ')
    

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self):
        return f"Node({self.name}, {self.children})"
    
    def print_tree(self, curr_path="/"):
        print(curr_path + self.name)
        for child in self.children:
            child.print_tree(curr_path + self.name + "/")
