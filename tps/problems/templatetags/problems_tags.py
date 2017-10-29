from django import template
from django.template.defaulttags import url, URLNode
from django.utils.html import format_html

register = template.Library()


class ProblemURLNode(template.Node):
    def __init__(self, problem_code, revision_slug, url_node):
        self.problem_code = problem_code
        self.revision_slug = revision_slug
        self.url_node = url_node
        self.url_node.args = [self.problem_code, self.revision_slug] + self.url_node.args

    def render(self, context):
        return self.url_node.render(context)


@register.tag
def problem_url(parser, token):
    return ProblemURLNode(
        parser.compile_filter("problem.code"),
        parser.compile_filter("revision_slug"),
        url(parser, token)
    )

@register.simple_tag(takes_context=True)
def commit_token(context):
    return format_html(
        "<input type='hidden' name='_commit_id' value='{}' />",
        context["revision"].commit_id
    )