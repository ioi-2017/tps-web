from django import template
from django.template.defaulttags import url, URLNode

register = template.Library()


class ProblemURLNode(template.Node):
    def __init__(self, problem_id, revision_id, url_node):
        self.problem_id = problem_id
        self.revision_id = revision_id
        self.url_node = url_node

    def render(self, context):
        self.url_node.args = [self.problem_id, self.revision_id] + self.url_node.args
        return self.url_node.render(context)


@register.tag
def problem_url(parser, token):
    return ProblemURLNode(
        parser.compile_filter("problem.id"),
        parser.compile_filter("revision.id"),
        url(parser, token)
    )
