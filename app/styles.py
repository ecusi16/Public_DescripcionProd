def style_hide_github_icon():
    return """
            <style>
            .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {
                display: none;
            }
            </style>
            """

def style_centrar_imagen():
    return """
            <style>
            .center-image {
                display: flex;
                justify-content: center;
            }
            </style>
            """

def style_tabla():
    return """
            <style>
            .dataframe tbody tr td {
                max-width: 150px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }
            .dataframe tbody tr td ul {
                padding-left: 20px;  /* Ajustar el margen izquierdo de las viñetas */
            }
            </style>
            """