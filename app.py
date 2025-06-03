if __name__ == "__main__":
    import flet as ft
    import sys

    sys.path.append("api")
    sys.path.append("ui")

    from ui.main_page import main

    ft.app(main)
