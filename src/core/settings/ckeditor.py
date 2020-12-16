CKEDITOR_CONFIGS = {
    'default': {
        # 'skin': 'moono',
        # 'skin': 'office2013',
        'toolbar_Basic': [
            ['Source', '-', 'Bold', 'Italic']
        ],
        'toolbar_YourCustomToolbarConfig': [
            # {'name': 'clipboard', 'items': ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
            # {'name': 'editing', 'items': ['Find', 'Replace', '-', 'SelectAll']},
            # '/',
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
            {'name': 'basicstyles',
             'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',]},
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {'name': 'insert',
             'items': ['Image', 'Flash', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak', 'Iframe']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            {'name': 'yourcustomtools', 'items': [
                'ShowBlocks',
                'Preview',
                'Maximize',
                 '-',
                 'Source',
            ]},
        ],
        'toolbar': 'YourCustomToolbarConfig',  # put selected toolbar config here
        # 'toolbarGroups': [{ 'name': 'document', 'groups': [ 'mode', 'document', 'doctools' ] }],
        # 'height': 291,
        # 'width': '100%',
        # 'filebrowserWindowHeight': 725,
        # 'filebrowserWindowWidth': 940,
        # 'toolbarCanCollapse': True,
        # 'mathJaxLib': '//cdn.mathjax.org/mathjax/2.2-latest/MathJax.js?config=TeX-AMS_HTML',
        'tabSpaces': 4,
        'font_names': ';'.join([
            'Arial/Arial, Helvetica, sans-serif',
            'Times New Roman/Times New Roman, Times, serif',
            'Verdana',
            'serif',
            'sans serif',
            'monospace',
            'cursive',
            'Athelas-Reg',
            'BrandonText-Regular',
            'BrandonText-Grotesque',
            'BrushScript-MT',
            # 'fantasy',
        ]),
        'contentsCss': ['/static/css/terms_and_condition/main.css', '/static/css/terms_and_condition/style.css'],
        'extraPlugins': ','.join([
            'uploadimage' # the upload image feature
            # your extra plugins here
            # 'div',
            # 'autolink',
            # 'autoembed',
            # 'embedsemantic',
            # 'autogrow',
            # # 'devtools',
            # 'widget',
            # 'lineutils',
            # 'clipboard',
            # 'dialog',
            # 'dialogui',
            # 'elementspath'
        ]),
    }
}
