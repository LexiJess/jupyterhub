import os
from collections import defaultdict

from pytablewriter import MarkdownTableWriter

from jupyterhub.scopes import scope_definitions

HERE = os.path.abspath(os.path.dirname(__file__))


class ScopeTableGenerator:
    def __init__(self):
        self.scopes = scope_definitions

    @classmethod
    def create_writer(cls, table_name, headers, values):
        writer = MarkdownTableWriter()
        writer.table_name = table_name
        writer.headers = headers
        writer.value_matrix = values
        writer.margin = 1
        return writer

    def _get_scope_relationships(self):
        """Returns a tuple of dictionary of all scope-subscope pairs and a list of just subscopes:

        ({scope: subscope}, [subscopes])

        used for creating hierarchical scope table in _parse_scopes()
        """
        pairs = []
        for scope in self.scopes.keys():
            if self.scopes[scope].get('subscopes'):
                for subscope in self.scopes[scope]['subscopes']:
                    pairs.append((scope, subscope))
            else:
                pairs.append((scope, None))
        subscopes = [pair[1] for pair in pairs]
        pairs_dict = defaultdict(list)
        for scope, subscope in pairs:
            pairs_dict[scope].append(subscope)
        return pairs_dict, subscopes

    def _get_top_scopes(self, subscopes):
        """Returns a list of highest level scopes
        (not a subscope of any other scopes)"""
        top_scopes = []
        for scope in self.scopes.keys():
            if scope not in subscopes:
                top_scopes.append(scope)
        return top_scopes

    def _parse_scopes(self):
        """Returns a list of table rows where row:
        [indented scopename string, scope description string]"""
        scope_pairs, subscopes = self._get_scope_relationships()
        top_scopes = self._get_top_scopes(subscopes)

        table_rows = []
        md_indent = "&nbsp;&nbsp;&nbsp;"

        def _add_subscopes(table_rows, scopename, depth=0):
            description = self.scopes[scopename]['description']
            meta_description = self.scopes[scopename].get('metadescription', '')
            if meta_description:
                description = description.rstrip('.') + f" _({meta_description})_."
            table_row = [f"{md_indent*depth}`{scopename}`", description]
            table_rows.append(table_row)
            for subscope in scope_pairs[scopename]:
                if subscope:
                    _add_subscopes(table_rows, subscope, depth + 1)

        for scope in top_scopes:
            _add_subscopes(table_rows, scope)

        return table_rows

    def write_table(self):
        """Generates the scope table in markdown format and writes it into scope-table.md file"""
        filename = f"{HERE}/scope-table.md"
        table_name = ""
        headers = ["Scope", "Grants permission to:"]
        values = self._parse_scopes()
        writer = self.create_writer(table_name, headers, values)

        title = "Table 1. Available scopes and their hierarchy"
        content = f"{title}\n{writer.dumps()}"
        with open(filename, 'w') as f:
            f.write(content)
        print(f"Generated {filename}.")
        print(
            "Run 'make clean' before 'make html' to ensure the built scopes.html contains latest scope table changes."
        )


def main():
    table_generator = ScopeTableGenerator()
    table_generator.write_table()


if __name__ == "__main__":
    main()
