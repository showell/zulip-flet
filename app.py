if __name__ == "__main__":
    import sys

    import flet as ft

    sys.path.append("api")
    sys.path.append("ui")

    from ui.main_page import main

    ft.app(main)
