from typing import List, Set

from django.template import Template
from django.template.base import Node, VariableNode


def get_template_variables(template_object: Template) -> Set[str]:
    variables: Set[str] = set()

    def traverse_nodes(nodes: List[Node]) -> None:
        for node in nodes:
            if isinstance(node, VariableNode):
                variables.add(node.filter_expression.token)
            elif hasattr(node, 'child_nodelists'):
                for child_nodes in node.child_nodelists:
                    traverse_nodes(child_nodes)

    traverse_nodes(template_object.nodelist)
    return variables
