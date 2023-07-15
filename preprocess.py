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

def node_text(node) -> str:
    return raw[node.start_byte:node.end_byte].decode("utf-8")

def process(node, Type: str | None = None):
    if Type is None: Type = node.type
    
    out = ""
    # print(Type)
    match Type:
        case "for_range_loop":
            out += process_for(node)

        # By default just print whatever parts of this node are unique and recursively process the children
        case other:
            start = node.start_byte
            for child in node.children:
                out += raw[start:child.start_byte].decode("utf8")
                out += process(child)
                start = child.end_byte
            out += raw[start:node.end_byte].decode("utf8")
    
    return out

def process_for(node):
    print("For discovered")
    return ""

print(process(tree.root_node))


