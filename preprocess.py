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
		# self.function_return = "void" # TODO: Probably want to save the full signature
		self.current_function = None
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

	def with_function(self, function):
		self.current_function = function
		return self

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


class QualifiedIdentifier:
	def __init__(self, name=""):
		self.namespace = []
		self.name = name
		self.templates = []
		self.trailing = ""

	def parse(name: str):
		out = QualifiedIdentifier()
		out.namespace = name.split("::")
		out.name = out.namespace[-1]
		out.namespace.pop(-1)
		out.templates = out.name.split("<")
		if len(out.templates) == 1: out.templates = []
		else:
			out.name = out.templates[0]
			out.templates = out.templates[1].split(",")
			trailing = out.templates[-1].split(">")
			out.templates[-1] = trailing[0]
			out.trailing = trailing[1]
		return out

	def __str__(self):
		ns = self.namespace[:]
		ns.append(self.name)
		ret = "::".join(ns)
		if len(self.templates) > 0:
			ret += f"<{','.join(self.templates)}>"
		return ret + self.trailing

class Function(QualifiedIdentifier):
	class Parameter:
		def __init__(self, t="", name="", default=""):
			self.name = name
			self.type = t
			self.default = default

		def parse(state: NodeState):
			out = Function.Parameter()
			out.type = process(state + state.node.children[0])
			out.name = process(state + state.node.children[1])
			if len(state.node.children) > 2:
				out.default = process(state + state.node.children[2])
			return out

		def __str__(self):
			return self.type + " " + self.name + "" if len(self.default) == 0 else (" = " + self.default)

	def __init__(self):
		self.parent = None
		self.toPrint = ""
		self.toPrintParameters = ""
		self.name = QualifiedIdentifier()
		self.return_type = ""
		self.trailing_return = False
		self.parameters = []
		self.originalParameters = None


	def parse(state: NodeState):
		node = state.node
		body = node.child_by_field_name("body")
		
		out = Function()
		out.parent = state.current_function

		out.return_type = process(state + node.children[-3])
		declarator = node.children[-2]
		out.name = QualifiedIdentifier.parse(process(state + declarator.children[0]))
		parameters = declarator.children[1]
		out.toPrintParameters = process(state + parameters)
		out.parameters = [Function.Parameter.parse(state + child) for child in parameters.children[1:-1]]

		trailingReturn = find_in_children(declarator, "trailing_return_type")
		if trailingReturn is not None:
			if out.return_type not in ["auto", "fn"]:
				raise RuntimeError("Trailing return type must follow auto or fn")
			out.return_type = process(state + trailingReturn.children[-1])

		body = process((state + body).with_function(out))
		out.toPrint = process_default_node(state.with_function(out)).replace(body, "")

		return out, body

	def parse_lambda(state: NodeState):
		node = state.node
		body = node.child_by_field_name("body")
		
		out = Function()
		out.parent = state.current_function
		out.return_type = "auto"
		out.name = QualifiedIdentifier()

		declarator = node.children[-2]
		parameters = declarator.children[1]
		out.toPrintParameters = process(state + parameters)
		out.parameters = [Function.Parameter.parse(state + child) for child in parameters.children[1:-1]]

		trailingReturn = find_in_children(declarator, "trailing_return_type")
		if trailingReturn is not None:
			if out.return_type not in ["auto", "fn"]:
				raise RuntimeError("Trailing return type must follow auto or fn")
			out.return_type = process(state + trailingReturn.children[-1])

		body = process((state + body).with_function(out))
		out.toPrint = process_default_node(state.with_function(out)).replace(body, "")

		return out, body

	def replace_parameters(self, newParams: list[Parameter]):
		self.originalParameters = self.parameters
		self.parameters = newParams
		newParamsStr = f"({', '.join([str(param) for param in newParams])})"
		self.toPrint = self.toPrint.replace(self.toPrintParameters, newParamsStr)
		self.toPrintParameters = newParamsStr

	def replace_return_type(self, newReturn: str):
		if self.trailing_return:
			self.toPrint = rreplace(self.toPrint, self.return_type, newReturn, 1)
		else: self.toPrint = self.toPrint.replace(self.return_type, newReturn, 1)
		self.return_type = newReturn

	def __str__(self):
		return self.toPrint



def process(state: NodeState, Type: str | None = None):
	if Type is None: Type = state.node.type

	out = ""
	match Type:
		case "function_definition" | "inline_method_definition" | "operator_cast_definition": #TODO: Does operator_cast work properly?
			out += process_function(state)

		case "lambda_expression":
			out += process_lambda(state)

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


function_signatures = ""

def process_function(state: NodeState):
	global function_signatures
	f, body = Function.parse(state)

	if f.name.name == "main"\
	  and len(f.name.namespace) == 0\
	  and len(f.parameters) <= 2\
	  and f.return_type in ["void", "fn", "auto", "int"]:
		f.replace_return_type("int")
		if len(f.parameters) == 1 and ("string" in f.parameters[0].type or f.parameters[0].type == "auto"):
			f.replace_parameters([Function.Parameter("int", "CPPE_argc"), Function.Parameter("const char**", "CPPE_argv")])
			if f.originalParameters[0].type == "auto": f.originalParameters[0].type = "std::vector<std::string_view>"
			body = body.replace("{", f"{{ CPPE_CONVERT_ARGC_ARGV_TO(CPPE_argc, CPPE_argv, {f.originalParameters[0].type}, {f.originalParameters[0].name})", 1)	

	if "CPPE_RETURN" in body:
		body = body.replace("{", f"{{ CPPE_DEFINE_PROPIGATOR_START(<{f.name}>, {f.return_type}, nullptr, 0)", 1)
		body = rreplace(body, "}", f"CPPE_DEFINE_PROPIGATOR_END(<{f.name}>, {f.return_type}) }}")
	else: body = body.replace("&CPPE_propigate_0", "nullptr")

	#TODO: Do we want to do anything with turning nested functions into lambdas?

	function_signatures += f.toPrint + ";\n"
	return f.toPrint + body

def process_lambda(state: NodeState):
	f, body = Function.parse_lambda(state)
	print(f.name)

	if "CPPE_RETURN" in body:
		body = body.replace("{", f"{{ CPPE_DEFINE_PROPIGATOR_START(<{f.name}>, {f.return_type}, nullptr, 0)", 1)
		body = rreplace(body, "}", f"CPPE_DEFINE_PROPIGATOR_END(<{f.name}>, {f.return_type}) }}")
	else: body = body.replace("&CPPE_propigate_0", "nullptr")

	return f.toPrint + body

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
			replacement = replacement.replace("{", f"{{ CPPE_DEFINE_LOOP_PROPIGATOR_AND_HELPER_START({label}, {state.current_function.return_type}, &CPPE_propigate_{state.labeled_depth - 1}, {state.labeled_depth});", 1)
			replacement = rreplace(replacement, "}", f"CPPE_DEFINE_LOOP_PROPIGATOR_END({label}, {state.current_function.return_type}); }}", 1)

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


implementation = process(NodeState().with_node(tree.root_node))
print("#include </home/joshuadahl/Dev/CPPE/library/CPPE.hpp>\n\n"\
	+ f"// Function Signatures\n\n{function_signatures}\n"\
	+"// Implementation\n\n\n" + apply_global_substitutions(implementation))
