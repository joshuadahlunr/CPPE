# Helpers

# from: https://stackoverflow.com/questions/2556108/rreplace-how-to-replace-the-last-occurrence-of-an-expression-in-a-string
def rreplace(s, old, new, occurrence = 1):
	li = s.rsplit(old, occurrence)
	return new.join(li)

# Extract the indentation of the last line of the provided block of text
def extract_ending_indent(text: str) -> str:
	last = text.split("\n")[-1]
	nonSpaceIndex = len(last) - len(last.lstrip())
	return last[0:nonSpaceIndex]

# Find the index of the given node in its parent
def index_in_parent(node) -> int:
	parent = node.parent
	for i, child in enumerate(parent.children):
		if child == node:
			return i
	return -1

# Get the parent of the given node (skipping any labeled_expression nodes)
def skip_labeled_parents(node):
	parent = node.parent
	while parent.type in ["labeled_expression", "labeled_statement", "possibly_labeled_control_flow_expression"]: parent = parent.parent
	return parent

# Given a node either it returns itself or it returns the node the labeled expression is wrapping!
def skip_labeled_expression_children(node):
	while node.type == "labeled_expression":
		node = node.children[2]
	return node

# Returns the provided string if it exists and had length... or returns the other thing
def str_or(string: str | None, other):
	if string is not None and len(string) > 0:
		return string
	return other

# Finds a child node of the given types 
def find_in_children(node, targetTypes: list[str] | str):
	if not isinstance(targetTypes, list): targetTypes = [targetTypes]
	queue = node.children[:] # Clone it!
	while len(queue) > 0:
		if queue[0].type in targetTypes:
			return queue[0]
		queue.extend(queue[0].children)
		queue.pop(0)
	return None

# Finds all child nodes of the given types
def find_all_in_children(node, targetTypes: list[str] | str):
	if not isinstance(targetTypes, list): targetTypes = [targetTypes]
	found = []
	queue = node.children[:] # Clone it!
	while len(queue) > 0:
		if queue[0].type in targetTypes:
			found.append(queue[0])
		queue.extend(queue[0].children)
		queue.pop(0)
	return found