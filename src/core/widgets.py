from ckeditor.widgets import CKEditorWidget as CKEditorWidget_org
from ckeditor.widgets import (
    mark_safe,
    DjangoJSONEncoder,
    force_str,
    flatatt,
    conditional_escape,
    json_encode,
)


class CKEditorWidget(CKEditorWidget_org):
    def render(self, name, value, attrs=None, renderer=None):
        if renderer is None:
            renderer = get_default_renderer()
        if value is None:
            value = ""
        final_attrs = self.build_attrs(self.attrs, attrs, name=name)
        self._set_config()
        external_plugin_resources = [
            [force_str(a), force_str(b), force_str(c)]
            for a, b, c in self.external_plugin_resources
        ]
        self.config['width'] = '100%'
        return mark_safe(
            renderer.render(
                "ck_editor_widget.html",
                {
                    "final_attrs": flatatt(final_attrs),
                    "value": conditional_escape(force_str(value)),
                    "id": final_attrs["id"],
                    "config": json_encode(self.config),
                    "external_plugin_resources": json_encode(external_plugin_resources),
                },
            )
        )
