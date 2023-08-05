from tree_sitter import Language, Parser
from helpers import *
import ast
import copy

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

class NodeState:
	def __init__(self):
		self.labeled_depth : int = 0
		self.function_return = "void" # TODO: Probably want to save the full signature
		self.node = None

	def clone(self):
		return copy.copy(self)

	def __pos__(self): # Unary +
		return self.clone()

	def with_node(self, node):
		self.node = node
		return self

	def clone_with_node(self, node):
		return self.clone().with_node(node)

	def __add__(self, node): # Binary +
		return self.clone_with_node(node)

	# Checks if the given expression node is within an expression
	def in_expression(self, node = None) -> bool:
		if node is None: node = self.node
		parent = skip_labeled_parents(node)
		if "init_declarator" in parent.type: return True
		if "expression" not in parent.type: return False
		if parent.type == "expression_statement": return False #TODO: Are there any cases where this causes issues?
		if "compound" in parent.type:
			return parent.child_by_field_name("return") == node\
				or parent.child_by_field_name("return").type in ["labeled_expression", "possibly_labeled_control_flow_expression"] #TODO: make sure this works
		return True

	# Replace all of the text for the given child with the given replacement
	def replace_child_in_output(self, node_out, child, replacement: str | None = None, from_back: bool = True):
		out = node_out
		if not isinstance(node_out, str):
			out = process_default_node(self + node_out)

		if isinstance(replacement, str) and len(replacement) > 0:
			defaultChild = child
			if not isinstance(child, str):
				defaultChild = process(self + child)
			if from_back: out = rreplace(out, defaultChild, replacement)
			else: out = out.replace(defaultChild, replacement, 1)
		return out

def process(state: NodeState, Type: str | None = None):
	if Type is None: Type = state.node.type

	out = ""
	match Type:
		case "expression_body":
			out += process_expression_body(state)

		case "switch_statement" | "try_statement":
			out += process_switch_try(state)

		case "case_statement":
			out += process_switch_case(state)

		case "catch_clause":
			out += process_catch_clause(state)

		case "compound_expression":
			out += process_compound_expression(state)

		case "if_statement":
			out += process_if(state)

		case "for_statement" | "while_statement" | "do_statement":
			out += process_standard_loop(state)

		case "for_range_loop":
			out += process_range_for(state)

		case "labeled_expression" | "possibly_labeled_control_flow_expression":
			out += process_labeled_expression(state)

		case "labeled_statement":
			out += process_labeled_statement(state)

		case "return_statement":
			out += process_return_statement(state)

		case "yield_statement":
			out += process_yield_statement(state)

		case "defer_statement":
			out += process_defer_statement(state)

		case "break_statement":
			out += process_break_statement(state)

		case "continue_statement":
			out += process_continue_statement(state)

		# By default just print whatever parts of this node are unique and recursively process the children
		case other:
			out += process_default_node(state)

	return out

def process_default_node(state: NodeState):
	node = state.node
	out = ""
	start = node.start_byte
	for child in node.children:
		out += raw[start:child.start_byte].decode("utf8")
		out += process(state + child)
		start = child.end_byte
	out += raw[start:node.end_byte].decode("utf8")
	return out

def process_expression_body(state: NodeState):
	return f"{{ return {process(state + state.node.children[1])}; }}" # We know the expression is always the second child!




def process_return_statement(state: NodeState):
	node = state.node
	usefulParent = node.parent.parent # .parent is usually a compound expression, .parent.parent is wrapping control flow #TODO: How many bugs does this assumption produce?
	expression = state.in_expression(node.parent.parent)
	if not expression: return process_default_node(state + node)
	return f"CPPE_RETURN({process(state + node.children[1])}, 0);".replace("(;, 0)", "({}, 0)")

def process_yield_statement(state: NodeState):
	# return process_default_node(state).replace("yield", "return")
	return f"CPPE_YIELD({process(state + state.node.children[1])}, 0);".replace("(;, 0)", "({}, 0)")

def process_break_statement(state: NodeState):
	label = state.node.child_by_field_name("label")
	if label is None: return process_default_node(state)
	return f"CPPE_BREAK({process(state + label)}, {state.labeled_depth});"

def process_continue_statement(state: NodeState):
	label = state.node.child_by_field_name("label")
	if label is None: return process_default_node(state)
	return f"CPPE_CONTINUE({process(state + label)}, {state.labeled_depth});"

def process_defer_statement(state: NodeState):
	return f"defer {{ {process(state + state.node.child_by_field_name('body'))} }};"

def process_compound_expression(state: NodeState, parent_valid : bool | None = None, label : str | None = None):
	node = state.node
	implicitReturn = node.child_by_field_name('return')
	out = process_default_node(state + node)

	if implicitReturn is not None:
		wrong = process(state + implicitReturn)
		out = rreplace(out, wrong, f"return {wrong};")
	# elif not "return" in out and state.in_expression(): # TODO: Not working!
	# 	raise RuntimeError("Compound expressions must (implicitly) return a value!")

	# if label is not None:
	# 	out = out.replace("{", "{ try {")
	# 	out = rreplace(out, "}", f"}} CPPE_DEFINE_CONTINUE_BREAK({label}) }}")

	valid_parents = ["function_definition", "lambda_expression"] # List of parents in which we don't need to wrap the code with a lambda!
	if parent_valid is None: parent_valid = node.parent.type in valid_parents
	if parent_valid:
		return out
	return "[&] " + out + "()"

def process_labeled_statement(state: NodeState):
	node = state.node
	label = process_default_node(state + node.child_by_field_name("label"))
	child = node.children[2] # We know the nested expression is always the third child

	match child.type:
		case "compound_expression":
			return process_compound_expression(state + child, None, label)

		case "for_statement" | "while_statement" | "do_statement":
			return label + ": " + process_standard_loop(state + child, label)

		case "for_range_loop":
			return label + ": " + process_range_for(state + child, label)

		case other:
			return process_default_node(state + node) # If it isn't a loop there is no need to specially process loop labeling

def process_labeled_expression(state: NodeState):
	node = state.node
	label = node.child_by_field_name("label")
	if label is None:
		return process(state + node.children[0]) # This is a possibly labeled_control_flow, so the only child should get passed through
	label = process_default_node(state + label)
	child = node.children[2] # We know the nested expression is always the third child

	match child.type:
		case "compound_expression":
			return process_compound_expression(state + child, None, label)

		case "for_statement" | "while_statement" | "do_statement":
			return process_standard_loop(state + child, label)

		case "for_range_loop":
			return process_range_for(state + child, label)

		case other: raise RuntimeError("Invalid type of labeled expression: " + child.type)

def process_switch_try(state: NodeState, label: str | None = None):
	node = state.node
	expression = state.in_expression()

	body = node.child_by_field_name("body")
	out = process_default_node(state + node) if node.type == "switch_expression" else state.replace_child_in_output(node, body, process_compound_expression(state + body, True, label), False)
	if expression:
		out = f"[&] {{ {out} }}()"
	return out

def process_switch_case(state: NodeState, label: str | None = None):
	node = state.node
	isExpression = state.in_expression()
	expression = node.child_by_field_name("expression")
	if expression is None:
		return process_default_node(state + node)
	
	return state.replace_child_in_output(node, expression, f": {process(state + expression)} break;")
	
def process_catch_clause(state: NodeState, label: str | None = None):
	body = state.node.child_by_field_name("body")
	return state.replace_child_in_output(state.node, body, process_compound_expression(state + body, True, label))

def process_if(state: NodeState, label: str | None = None):
	node = state.node
	expression = state.in_expression()

	consequence = node.child_by_field_name("consequence")
	out = state.replace_child_in_output(node, consequence, process_compound_expression(state + consequence, True, label), False)
	if expression:
		out = f"[&] {{ {out} }}()"
	return out

def process_range_for(state: NodeState, label: str | None = None):
	node = state.node
	numChildren = len(node.children)
	out = ""
	start = node.start_byte
	for i, child in enumerate(node.children):
		out += raw[start:child.start_byte].decode("utf8")
		match i:
			# We split out the nodes like this so we can surgically replace in with : and foreach with for
			case 0: out += process(state + child).replace("foreach", "for")
			case 4: out += process(state + child).replace("in", ":") if numChildren <= 8 else process(state + child) # in could be in either one of these depending on if there is an initializer or not!
			case 5: out += process(state + child) if numChildren <= 8 else process(state + child).replace("in", ":") # in could be in either one of these depending on if there is an initializer or not!
			case other: out += process(state + child)
		start = child.end_byte
	out += raw[start:node.end_byte].decode("utf8")

	# Apply all of the replacements we would apply to other types of loops!
	return process_standard_loop(state + node, label, out)

def process_standard_loop(state: NodeState, label: str | None = None, out: str | None = None):
	node = state.node
	expression = state.in_expression()

	# TODO: Uncomment this optimization when we no longer need to test code around it!
	# # Make sure we only pay for labeled continue/breaks if we use them!
	# cbs = find_all_in_children(node, ["continue_statement", "break_statement"])
	# cbs = [e for e in cbs if e.child_by_field_name("label") is not None]
	# if len(cbs) == 0:
	# 	label = None

	state.labeled_depth += 1 if label is not None else 0

	body = node.child_by_field_name("body")
	if not expression:
		bodyText = process(state + body)
		replacement = bodyText
		if label is not None:
			if not bodyText.strip().startswith("{"):
				replacement = "{ " + replacement + " }"
			replacement = replacement.replace("{", f"{{ CPPE_DEFINE_LOOP_PROPIGATOR_AND_HELPER_START({label}, {state.function_return}, &CPPE_propigate_{state.labeled_depth - 1}, {state.labeled_depth});", 1)
			replacement = rreplace(replacement, "}", f"CPPE_DEFINE_LOOP_PROPIGATOR_END({label}, {state.function_return}); }}", 1)
		
		out = state.replace_child_in_output(str_or(out, node), bodyText, replacement)
		# TODO: Why do inner labels disappear?
		

	else:
		if body.type == "compound_expression":
			bodyText = process(state + body)
		else: bodyText = f"[&] {{ return {process(state + body)}; }}()"
		loopBody = f"{{ CPPE_out.emplace_back(CPPE_loop_body()); }}"
		if label is not None:
			loopBody = loopBody.replace("{", f"{{ CPPE_DEFINE_LOOP_PROPIGATOR_START({label}, void, &CPPE_propigate_helper_{state.labeled_depth - 1}, {state.labeled_depth});")\
				.replace("CPPE_propigate_helper_0", "CPPE_propigate_0")
			loopBody = rreplace(loopBody, "}", f"CPPE_DEFINE_LOOP_PROPIGATOR_END({label}, void) }};")

		out = state.replace_child_in_output(str_or(out, node), body, loopBody)
		
		bodyLine = " " #TODO: Implement
		if label is not None: bodyLine = f"CPPE_DEFINE_LOOP_HELPER_PROPIGATOR({state.labeled_depth})" + bodyLine
		conditionLine = "" #TODO: Implement
		out = f"[&] {{ {bodyLine} auto CPPE_loop_body = {bodyText[0:-2]}; std::vector<decltype(CPPE_loop_body())> CPPE_out;\n{conditionLine}{extract_ending_indent(bodyText)}{out} return CPPE_out; }}()"

	return out



def apply_global_substitutions(processed: str) -> str:
	return processed.replace(";;", ";").replace("<-", "=")

print("#include </home/joshuadahl/Dev/CPPE/library/CPPE.hpp>\n\n"\
	+ apply_global_substitutions(process(NodeState().with_node(tree.root_node))))
