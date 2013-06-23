# -*- coding: utf-8 -*-

from PyQt4.QtCore import QObject
from collections import defaultdict

from ninja_ide.core import settings
from ninja_ide.gui.ide import IDE

#NINJA-IDE Menus
#from ninja_ide.gui.menus import menu_about
#from ninja_ide.gui.menus import menu_file
#from ninja_ide.gui.menus import menu_edit
#from ninja_ide.gui.menus import menu_view
#from ninja_ide.gui.menus import menu_plugins
#from ninja_ide.gui.menus import menu_project
#from ninja_ide.gui.menus import menu_source

SEC01 = 100
SEC02 = 200
SEC03 = 300
SEC04 = 400
SEC05 = 500
SEC06 = 600
SEC07 = 700
SEC08 = 800
SEC09 = 900
SEC10 = 1000


def menu_add_section(menu, section_parts):
    """
    each_part is expected to be a tuple of
    (QIcon, String, bool) containing respectively the icon, text and flag
    indicating if this is an action
    """
    for each_part, weight in section_parts:
        icon, text, action = each_part
        if action:
            add = menu.addAction
        else:
            add = menu.addMenu
        if icon:
            add(icon, text)
        else:
            add(text)
    #FIXME: This appends a separator at the end of each menu
    menu.addSeparator()


class _MenuBar(QObject):

    def __init__(self):
        super(_MenuBar, self).__init__()
        self._roots = {}
        self._children = {}
        self._menu_refs = {}

        IDE.register_service('menu_bar', self)
        IDE.register_service('menu_file', self._menuFile)
        IDE.register_service('menu_view', self._menuView)

        menu_file_connections = (
            {'target': 'main_container',
            'signal_name': 'recentTabsModified(QStringList)',
            'slot': self._menuFile.update_recent_files},
        )
        IDE.register_signals('menu_file', menu_file_connections)

    def add_root(self, root_name, root_weight=None):
        """
        Add a root menu with desired weight or at end of list
        """
        if root_name not in self._roots:
            if root_weight is None:
                root_weight = sorted(self._roots.values())[-1] + 1
            self._roots[root_name] = root_weight

    def get_root(self):
        iter_items = self._roots.iteritems()
        iter_items.sort(key=lambda x: x[1])
        return iter_items

    def add_child(self, root_name, child_name, child, weight):
        #FIXME: We should also add plugin namespace for grouping per plugin
        child_path = (root_name, child_name)
        if child_path not in self._children:
            self.add_root(root_name)
            self._children[child_path] = (child, weight)

    def get_children_of(self, parent):
        children = defaultdict(lambda: [])
        for each_child in self._children:
            if parent == each_child[0]:
                child, weight = self._children[each_child]
                children[weight / 100].append((child, weight))

        return children

    def install(self):
        ide = IDE.get_service('ide')
        #menuBar is the actual QMenuBar object from IDE which is a QMainWindow
        menubar = ide.menuBar()
        for each_menu in self.get_root():
            menu_object = menubar.addMenu(self.tr(each_menu))
            self._menu_refs[each_menu] = menu_object
            all_children = self.get_children_of(each_menu)
            for each_child_grp_key in sorted(all_children):
                each_child_grp = all_children[each_child_grp_key]
                menu_add_section(menu_object, sorted(each_child_grp,
                                                key=lambda x: x[1]))

        #FIXME: Now move all this to respective containers and do a builder
        #FIXME: ... for toolbar

        file_ = menubar.addMenu(self.tr("&File"))
        edit = menubar.addMenu(self.tr("&Edit"))
        view = menubar.addMenu(self.tr("&View"))
        source = menubar.addMenu(self.tr("&Source"))
        project = menubar.addMenu(self.tr("&Project"))
        self.pluginsMenu = menubar.addMenu(self.tr("&Addins"))
        about = menubar.addMenu(self.tr("Abou&t"))

        #The order of the icons in the toolbar is defined by this calls
        self._menuFile.install_menu(file_, ide.toolbar, ide)
        self._menuView.install_menu(view, ide.toolbar, ide)
        self._menuEdit.install_menu(edit, ide.toolbar)
        self._menuSource.install_menu(source)
        self._menuProject.install_menu(project, ide.toolbar)
        self._menuPlugins.install_menu(ide.pluginsMenu)
        self._menuAbout.install_menu(about)

        self.load_toolbar(ide)

    def load_toolbar(self, ide):
        #FIXME: Do the same as above to add items to toolbar
        toolbar = ide.toolbar
        toolbar.clear()
        toolbar_items = {}
        toolbar_items.update(self._menuFile.toolbar_items)
        toolbar_items.update(self._menuView.toolbar_items)
        toolbar_items.update(self._menuEdit.toolbar_items)
        toolbar_items.update(self._menuSource.toolbar_items)
        toolbar_items.update(self._menuProject.toolbar_items)

        for item in settings.TOOLBAR_ITEMS:
            if item == 'separator':
                toolbar.addSeparator()
            else:
                tool_item = toolbar_items.get(item, None)
                if tool_item is not None:
                    toolbar.addAction(tool_item)
        #load action added by plugins, This is a special case when reload
        #the toolbar after save the preferences widget
        for toolbar_action in settings.get_toolbar_item_for_plugins():
            toolbar.addAction(toolbar_action)


#menu = _MenuBar()
