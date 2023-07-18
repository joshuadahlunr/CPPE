# Helpers

# from: https://stackoverflow.com/questions/2556108/rreplace-how-to-replace-the-last-occurrence-of-an-expression-in-a-string
def rreplace(s, old, new, occurrence = 1):
	li = s.rsplit(old, occurrence)
	return new.join(li)

def extract_ending_indent(text: str) -> str:
	last = text.split("\n")[-1]
	nonSpaceIndex = len(last) - len(last.lstrip())
	return last[0:nonSpaceIndex]

def index_in_parent(node) -> int:
	parent = node.parent
	for i, child in enumerate(parent.children):
		if child == node:
			return i
	return -1

def determine_if_control_flow_is_expression(node) -> bool:
	parent = node.parent
	while parent.type == "labeled_expression": parent = parent.parent
	if "init_declarator" in parent.type: return True
	if "expression" not in parent.type: return False
	if "compound" in parent.type:
		if node.parent.child_by_field_name("return") == node:
			return True #TODO: make sure this works
	return True

def skip_labeled_expression_children(node):
	while node.type == "labeled_expression":
		node = node.children[2]
	return node




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
			out.extend(process_if(node))

		case "for_statement":
			out += process_for(node)

		case "for_range_loop":
			out += process_for(node)

		case "while_statement":
			out += process_while(node)

		case "do_statement":
			out += process_do_while(node)

		case "try_statement":
			out += process_do_while(node)

		case "_possibly_labeled_control_flow_expression":
			out += process_labeled_expression(node)

		case "labeled_expression":
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
			return process_compound_expression(node, None, label)

		case "while_statement":
			return process_while(child, label)

		case other: raise RuntimeError("Invalid type of labeled expression: " + child.type)


def process_switch(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)
	print(f"switch discovered {expression}")
	return ""

def process_if(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)
	print(f"if discovered {expression}")
	return ""

def process_for(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)
	print(f"For discovered {expression}")
	return ""

def process_while(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)

	out = process_default_node(node)
	body = node.child_by_field_name("body")
	defaultBody = process(body)
	if not expression:
		if(body.type == "compound_expression"):
			out = rreplace(out, defaultBody, process_compound_expression(body, True, label))

	else:
		print(f"body: {body.type}")
		if body.type == "compound_expression":
			body = defaultBody
		else: body = f"[&] {{ return {defaultBody}; }}()"
		loopBody = f"{{ __out.emplace_back(__loop_body()); }}"
		if label is not None:
			loopBody = rreplace(loopBody, "}", f"CPPE_CONTINUE_BREAK({label}) }}")

		# out = f"[&] {{ std::vector<{type}> out;#line {whatever}\n{out}" #TODO: Implement
		out = rreplace(out, defaultBody, loopBody)
		out = f"[&] {{ auto __loop_body = {body[0:-2]}; std::vector<decltype(__loop_body())> __out;\n{extract_ending_indent(body)}{out} return __out; }}()"

	return out

def process_do_while(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)
	print(f"do-while discovered {expression}")
	return ""

def process_try(node, label: str | None = None):
	expression = determine_if_control_flow_is_expression(node)
	print(f"try discovered {expression}")
	return ""



def apply_substitutions(processed: str) -> str:
	return processed.replace(";;", ";").replace("<-", "=")

print(apply_substitutions(process(tree.root_node)))
