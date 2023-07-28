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
def skip_labeled_expression_parents(node):
	parent = node.parent
	while parent.type == "labeled_expression": parent = parent.parent
	return parent

# Checks if the given expression node is within an expression
def determine_if_node_in_expression(node) -> bool:
	parent = skip_labeled_expression_parents(node)
	if "init_declarator" in parent.type: return True
	if "expression" not in parent.type: return False
	if "compound" in parent.type:
		return parent.child_by_field_name("return") == node #TODO: make sure this works
	return True

# Given a node either it returns itself or it returns the node the labeled expression is wrapping!
def skip_labeled_expression_children(node):
	while node.type == "labeled_expression":
		node = node.children[2]
	return node

# Replace all of the text for the given child with the given replacement
def replace_child_in_output(node_out, child, replacement: str | None = None, from_back: bool = True):
	out = node_out
	if not isinstance(node_out, str):
		out = process_default_node(node_out)

	if isinstance(replacement, str) and len(replacement) > 0:
		defaultChild = process(child)
		if from_back: out = rreplace(out, defaultChild, replacement)
		else: out = out.replace(defaultChild, replacement, 1)
	return out

# Returns the provided string if it exists and had length... or returns the other thing
def str_or(string: str | None, other):
	if string is not None and len(string) > 0:
		return string
	return other



from tree_sitter import Language, Parser
import ast

Language.build_library(
	# Store the library in the `build` directory
	'build/cppe.so',

	# Include one or more languages
	[
		'tree-sitter-cppe',
	]
)

language = Language('build/cppe.so', 'cppe')

parser = Parser()
parser.set_language(language)

tree = None
raw = None
with open("tree-sitter-cppe/examples/hello.cppe") as f:
	raw = f.read().encode("utf8")
	tree = parser.parse(raw)



control_flow_node_types = ["switch_statement", "compound_expression", "if_statement", "for_statement", "for_range_loop", "while_statement", "do_statement", "try_statement", "_possibly_labeled_control_flow_expression"]

def process(node, Type: str | None = None):
	if Type is None: Type = node.type

	out = ""
	# print(Type)
	match Type:
		case "expression_body":
			out += process_expression_body(node)

		case "switch_statement":
			out += process_switch(node)

		case "compound_expression":
			out += process_compound_expression(node)

		case "if_statement":
			out += process_if(node)

		case "for_statement" | "while_statement" | "do_statement":
			out += process_standard_loop(node)

		case "for_range_loop":
			out += process_range_for(node)
			
		case "try_statement":
			out += process_try(node)

		case "labeled_expression" | "_possibly_labeled_control_flow_expression":
			out += process_labeled_expression(node)

		case "return_statement":
			print("return is not yet supported!")
		
		case "yield_statement":
			print("yield is not yet supported!")

		case "defer_statement":
			raise RuntimeError("defer is not yet supported!")

		case "break_statement":
			print("break is not yet supported!")

		case "continue_statement":
			print("continue is not yet supported!")

		# By default just print whatever parts of this node are unique and recursively process the children
		case other:
			out += process_default_node(node)

	return out

def process_default_node(node):
	out = ""
	start = node.start_byte
	for child in node.children:
		out += raw[start:child.start_byte].decode("utf8")
		out += process(child)
		start = child.end_byte
	out += raw[start:node.end_byte].decode("utf8")
	return out

def process_expression_body(node):
	return f"{{ return {process(node.children[1])}; }}" # We know the expression is always the second child!




def process_compound_expression(node, parent_valid : bool | None = None, label : str | None = None):
	implicitReturn = node.child_by_field_name('return')
	out = process_default_node(node)

	if implicitReturn is not None:
		wrong = process(implicitReturn)
		out = rreplace(out, wrong, f"return {wrong};")
	# elif not "return" in out and determine_if_node_in_expression(node): # TODO: Not working!
	# 	raise RuntimeError("Compound expressions must (implicitly) return a value!")

	if label is not None:
		out = rreplace(out, "}", f"CPPE_CONTINUE_BREAK({label}) }}")

	valid_parents = ["function_definition", "lambda_expression"] # List of parents in which we don't need to wrap the code with a lambda!
	if parent_valid is None: parent_valid = node.parent.type in valid_parents
	if parent_valid:
		return out
	return "[&] " + out + "()"

def process_labeled_expression(node):
	label = process_default_node(node.child_by_field_name("label"))
	child = node.children[2] # We know the nested expression is always the third child

	match child.type:
		case "compound_expression":
			return process_compound_expression(child, None, label)

		case "for_statement" | "while_statement" | "do_statement":
			return process_standard_loop(child, label)

		case "for_range_loop":
			return process_range_for(child, label)

		case other: raise RuntimeError("Invalid type of labeled expression: " + child.type)


def process_switch(node, label: str | None = None):
	expression = determine_if_node_in_expression(node)
	print(f"switch discovered {expression}")
	return ""

def process_if(node, label: str | None = None):
	expression = determine_if_node_in_expression(node)
	print(f"if discovered {expression}")
	return ""

def process_range_for(node, label: str | None = None):
	numChildren = len(node.children)
	out = ""
	start = node.start_byte
	for i, child in enumerate(node.children):
		out += raw[start:child.start_byte].decode("utf8")
		match i:
			# We split out the nodes like this so we can surgically replace in with : and foreach with for
			case 0: out += process(child).replace("foreach", "for")
			case 4: out += process(child).replace("in", ":") if numChildren <= 8 else process(child) # in could be in either one of these depending on if there is an initializer or not!
			case 5: out += process(child) if numChildren <= 8 else process(child).replace("in", ":") # in could be in either one of these depending on if there is an initializer or not!
			case other: out += process(child)
		start = child.end_byte
	out += raw[start:node.end_byte].decode("utf8")
	
	# Apply all of the replacements we would apply to other types of loops!
	return process_standard_loop(node, label, out)

def process_standard_loop(node, label: str | None = None, out: str | None = None):
	expression = determine_if_node_in_expression(node)

	body = node.child_by_field_name("body")
	if not expression:
		out = replace_child_in_output(str_or(out, node), body, process_compound_expression(body, True, label))

	else:
		if body.type == "compound_expression":
			bodyText = process(body)
		else: bodyText = f"[&] {{ return {process(body)}; }}()"
		loopBody = f"{{ __out.emplace_back(__loop_body()); }}"
		if label is not None:
			loopBody = rreplace(loopBody, "}", f"CPPE_CONTINUE_BREAK({label}) }}")

		out = replace_child_in_output(str_or(out, node), body, loopBody)
		# out = rreplace(out, defaultBody, loopBody)
		bodyLine = "" #TODO: Implement
		conditionLine = "" #TODO: Implement
		out = f"[&] {{ {bodyLine} auto __loop_body = {bodyText[0:-2]}; std::vector<decltype(__loop_body())> __out;\n{conditionLine}{extract_ending_indent(bodyText)}{out} return __out; }}()"

	return out

def process_try(node, label: str | None = None):
	expression = determine_if_node_in_expression(node)
	print(f"try discovered {expression}")
	return ""



def apply_global_substitutions(processed: str) -> str:
	return processed.replace(";;", ";").replace("<-", "=")

print(apply_global_substitutions(process(tree.root_node)))
