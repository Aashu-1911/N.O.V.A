from enum import Enum
import uiautomation as auto

class ControlType(Enum):
    BUTTON = "Button"
    EDIT = "Edit"
    TEXT = "Text"
    COMBOBOX = "ComboBox"
    CHECKBOX = "CheckBox"
    RADIOBUTTON = "RadioButton"
    MENU = "Menu"
    MENUITEM = "MenuItem"
    TOOLBAR = "ToolBar"
    TREE = "Tree"
    TREEITEM = "TreeItem"
    TAB = "Tab"
    TABITEM = "TabItem"
    LIST = "List"
    LISTITEM = "ListItem"
    TABLE = "Table"
    DATAGRID = "DataGrid"
    PANE = "Pane"
    GROUP = "Group"
    DIALOG = "Dialog"
    STATUSBAR = "StatusBar"
    PROGRESSBAR = "ProgressBar"
    HYPERLINK = "Hyperlink"
    IMAGE = "Image"
    SCROLLBAR = "ScrollBar"
    WINDOW = "Window"

    def to_uia_type(self) -> int:
        """Map enum values to native uiautomation ControlType IDs."""
        mapping = {
            ControlType.BUTTON: auto.ControlType.ButtonControl,
            ControlType.EDIT: auto.ControlType.EditControl,
            ControlType.TEXT: auto.ControlType.TextControl,
            ControlType.COMBOBOX: auto.ControlType.ComboBoxControl,
            ControlType.CHECKBOX: auto.ControlType.CheckBoxControl,
            ControlType.RADIOBUTTON: auto.ControlType.RadioButtonControl,
            ControlType.MENU: auto.ControlType.MenuControl,
            ControlType.MENUITEM: auto.ControlType.MenuItemControl,
            ControlType.TOOLBAR: auto.ControlType.ToolBarControl,
            ControlType.TREE: auto.ControlType.TreeControl,
            ControlType.TREEITEM: auto.ControlType.TreeItemControl,
            ControlType.TAB: auto.ControlType.TabControl,
            ControlType.TABITEM: auto.ControlType.TabItemControl,
            ControlType.LIST: auto.ControlType.ListControl,
            ControlType.LISTITEM: auto.ControlType.ListItemControl,
            ControlType.TABLE: auto.ControlType.TableControl,
            ControlType.DATAGRID: auto.ControlType.DataGridControl,
            ControlType.PANE: auto.ControlType.PaneControl,
            ControlType.GROUP: auto.ControlType.GroupControl,
            ControlType.DIALOG: auto.ControlType.WindowControl,
            ControlType.STATUSBAR: auto.ControlType.StatusBarControl,
            ControlType.PROGRESSBAR: auto.ControlType.ProgressBarControl,
            ControlType.HYPERLINK: auto.ControlType.HyperlinkControl,
            ControlType.IMAGE: auto.ControlType.ImageControl,
            ControlType.SCROLLBAR: auto.ControlType.ScrollBarControl,
            ControlType.WINDOW: auto.ControlType.WindowControl,
        }
        return mapping[self]


class WindowState(Enum):
    NORMAL = "Normal"
    MINIMIZED = "Minimized"
    MAXIMIZED = "Maximized"
