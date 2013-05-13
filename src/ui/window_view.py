
#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Wang Yaohua
# 
# Author:     Wang Yaohua <mr.asianwang@gmail.com>
# Maintainer: Wang Yaohua <mr.asianwang@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from dtk.ui.dialog import DialogBox, DIALOG_MASK_GLASS_PAGE, OpenFileDialog, SaveFileDialog, ConfirmDialog
from dtk.ui.button import ImageButton
from dtk.ui.treeview import TreeView, TreeItem
from dtk.ui.window import Window
from dtk.ui.titlebar import Titlebar
from dtk.ui.label import Label
from dtk.ui.menu import Menu
from dtk.ui.draw import draw_text, draw_pixbuf, draw_vlinear
from dtk.ui.entry import InputEntry
from dtk.ui.combo import ComboBox
from dtk.ui.utils import container_remove_all, place_center
from dtk.ui.skin import SkinWindow
from dtk.ui.cache_pixbuf import CachePixbuf

import xdg
from ui.skin import app_theme
from ui.listview_factory import ListviewFactory
from ui.utils import draw_line, draw_single_mask
from notification_db import db
from blacklist import blacklist

import gtk
import pango
import gobject
from datetime import datetime, timedelta


TIME = 0
MESSAGE = 1

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TITLEBAR_HEIGHT = 25
TOOLBAR_HEIGHT = 40
INFO_AREA_HEIGHT = 40
TOOLBAR_ENTRY_HEIGHT = 24

STROKE_LINE_COLOR = (0.8, 0.8, 0.8)

class ToolbarSep(gtk.HBox):
    
    def __init__(self):
        '''
        docso
        '''
        gtk.HBox.__init__(self)
        self.set_size_request(1, -1)
        self.connect("expose-event", self.expose_event)
        
    def expose_event(self, widget, event):
        '''
        docs
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # sep height is 2/3 of hbox
        x = rect.x 
        y = rect.y + rect.height / 6
        width = 1
        height = rect.height * 2 / 3
        
        draw_vlinear(cr, x, y, width, height, [(0, ("#ffffff", 0)),
                                               (0.5, ("#2b2b2b", 0.5)), 
                                               (1, ("#ffffff", 0))])
        
        
TOOLBAR_ITEM_HEIGHT = 30
TOOLBAR_ITEM_WIDTH = 70

class ToolbarItem(gtk.Button):
    '''
    class docs
    '''
	
    def __init__(self, pixbuf, content=""):
        
        '''
        init docs
        '''
        gtk.Button.__init__(self)
        self.pixbuf = pixbuf
        self.content = content
        
        self.set_size_request(TOOLBAR_ITEM_WIDTH, TOOLBAR_ITEM_HEIGHT)
        self.connect("expose-event", self.on_expose_event)
        
    def get_pixbuf_size(self):
        return (self.pixbuf.get_width(), self.pixbuf.get_height())        

    def on_expose_event(self, widget, event):
        '''
        docs
        '''
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if widget.state == gtk.STATE_NORMAL:
            cr.set_source_rgba(0, 0, 0, 0)
        elif widget.state == gtk.STATE_PRELIGHT:
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        elif widget.state == gtk.STATE_ACTIVE:
            cr.set_source_rgb(0.5, 0.5, 0.5)
            
        cr.rectangle(*rect)
        cr.fill()
        
        draw_pixbuf(cr, self.pixbuf, rect.x, rect.y + 5)
        
        (pixbuf_width, pixbuf_height) = self.get_pixbuf_size()
        draw_text(cr, self.content,
                  rect.x + pixbuf_width + 2,
                  rect.y + 8,
                  rect.width - pixbuf_width,
                  rect.height - pixbuf_height
                  )
            
        return True
            
        
    
gobject.type_register(ToolbarItem)        
    
class SearchEntry(InputEntry):
    
    def __init__(self, *args, **kwargs):


        entry_button = ImageButton(
            app_theme.get_pixbuf("search_normal.png"),
            app_theme.get_pixbuf("search_hover.png"),
            app_theme.get_pixbuf("search_press.png")
            )
        
        super(SearchEntry, self).__init__(action_button=entry_button, *args, **kwargs)        
        
        self.action_button = entry_button
        self.set_size(150, TOOLBAR_ENTRY_HEIGHT + 2)
        
gobject.type_register(SearchEntry)        



pixbuf_blacklist_white = app_theme.get_pixbuf("blacklist_white.png").get_pixbuf()
pixbuf_blacklist_grey = app_theme.get_pixbuf("blacklist_grey.png").get_pixbuf()

pixbuf_arrow_down = app_theme.get_pixbuf("down_normal.png").get_pixbuf()
pixbuf_arrow_right = app_theme.get_pixbuf("right_normal.png").get_pixbuf()

class TreeViewItem(TreeItem):
    
    def __init__(self, title, is_parent=False, is_in_blacklist=False):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        
        self.title = title
        
        self.item_height = 26
        self.item_width = 200
        
        self.draw_padding_x = 10
        self.draw_padding_y = 10
        
        self.column_index = 0

        self.is_hover = False        
        self.is_select = False
        self.is_highlight = False
        
        self.is_parent = is_parent
        self.is_in_blacklist = is_in_blacklist
        
        if is_parent:
            self.row_index = 0
        else:    
            self.row_index = 1
            
            
        self.child_offset = 15
    
    def get_title(self):
        return self.title
        
    def add_child_items(self, items):
        self.child_items = items
        self.expand()
        
    def get_height(self):    
        return self.item_height
    
    def get_column_widths(self):
        return [self.item_width,]
    
    def get_column_renders(self):
        return (self.render_title,)
    
    def unselect(self):
        self.is_select = False
        self.emit_redraw_request()
        
    def emit_redraw_request(self):    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def expand(self):
        self.is_expand = True
        
        if self.child_items:
            self.add_items_callback(self.child_items, self.row_index + 1)
                
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def unexpand(self):
        self.is_expand = False
        
        if self.child_items:
            self.delete_items_callback(self.child_items)
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

            
    def select(self):        
        self.is_select = True
        self.emit_redraw_request()
        
    def render_title(self, cr, rect):        
        # Draw select background.
        rect.width -= 2
        
        if not self.is_parent:
            if self.is_highlight:    
                draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemSelect")
            elif self.is_hover:
                draw_single_mask(cr, rect.x, rect.y, rect.width, rect.height, "globalItemHover")
        
            if self.is_highlight:
                text_color = "#FFFFFF"
            else:    
                text_color = "#000000"
        else:
            text_color = "#000000"
            
        # draw arrow and blacklist icon
        left_pixbuf_width = 18            
        if not self.is_parent:    
            rect.x += self.child_offset
            rect.width -= self.child_offset
            
            if self.is_in_blacklist:
                if self.is_highlight:
                    pixbuf = pixbuf_blacklist_white
                else:
                    pixbuf = pixbuf_blacklist_grey
            else:
                pixbuf = None
        
            if pixbuf:
                draw_pixbuf(cr, pixbuf, rect.x + self.draw_padding_x, rect.y + 5)
        else:
            left_pixbuf_width = 0
            
            if self.is_expand:
                pixbuf = pixbuf_arrow_down
            else:
                pixbuf = pixbuf_arrow_right
                
            draw_pixbuf(cr, pixbuf, rect.x + rect.width - 80, rect.y + 10)

            
        temp_text = self.title if self.is_parent else " - " + self.title
        draw_text(cr, temp_text,
                  rect.x + self.draw_padding_x + left_pixbuf_width, 
                  rect.y,
                  rect.width - self.draw_padding_x * 2, 
                  rect.height, 
                  text_color = text_color,
                  alignment=pango.ALIGN_LEFT)    
        
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.emit_redraw_request()
        
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.emit_redraw_request()
        
    
    def highlight(self):    
        self.is_highlight = True
        self.emit_redraw_request()
        
    def unhighlight(self):    
        self.is_highlight = False
        self.emit_redraw_request()
        
                              
timedelta_dict = {
    "All" : timedelta.max,
    "Today" : timedelta(days=1),
    "Last Week" : timedelta(weeks=1),
    "Latest month" : timedelta(days=31),
    "The last three months" : timedelta(days=93),
    "The recent year" : timedelta(days=365)
    }
    

class DetailWindow(Window):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        Window.__init__(self)
        self.set_size_request(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_position(gtk.WIN_POS_CENTER)
        self.resizable = True

        self.classified_items = None
        self.__init_pixbuf()
        
        self.main_box = gtk.VBox()
        self.titlebar_box = gtk.HBox()
        self.toolbar_box = gtk.HBox()
        self.toolbar_box.set_size_request(-1, TOOLBAR_HEIGHT)
        self.toolbar_box.connect("expose-event", self.on_toolbar_expose_event)
        
        self.main_view_box = gtk.HBox()
        self.main_view_box.set_size_request(WINDOW_WIDTH, 
                                            WINDOW_HEIGHT - TITLEBAR_HEIGHT - TOOLBAR_HEIGHT - INFO_AREA_HEIGHT)
        self.main_view_box.connect("expose-event", self.on_main_view_box_expose_event)
        
        self.add_titlebar()        
        self.treeview_box = gtk.VBox()
        self.main_view_box.pack_start(self.treeview_box, False, False)
        self.listview_box = gtk.VBox()
        self.main_view_box.pack_start(self.listview_box, True, True)
        self.refresh_view() #add treeview and listview 

        self.info_area_box = gtk.HBox()
        info_area_box_align = gtk.Alignment(0.5, 0.5, 1, 1)
        info_area_box_align.set_padding(6, 0, 100, 0)
        self.status_bar = Label()
        self.status_bar.set_size_request(100, -1)
        info_area_box_align.add(self.status_bar)
        self.info_area_box.pack_start(info_area_box_align, False, False)
        
        self.main_box.pack_start(self.toolbar_box, False, False)
        self.main_box.pack_start(self.main_view_box, False, False)
        self.main_box.pack_start(self.info_area_box, False, False)
        
        main_box_align = gtk.Alignment(0.5, 0.5, 1, 1)        
        main_box_align.set_padding(7, 7, 7, 7)
        main_box_align.add(self.main_box)

        self.window_frame.pack_start(self.titlebar_box, False, False)
        self.window_frame.pack_start(main_box_align)
        
        

    def __init_pixbuf(self):
        self.import_btn_pixbuf = gtk.gdk.pixbuf_new_from_file(app_theme.get_theme_file_path("image/toolbar_import.png"))
        self.export_btn_pixbuf = gtk.gdk.pixbuf_new_from_file(app_theme.get_theme_file_path("image/toolbar_export.png"))
        self.delete_btn_pixbuf = gtk.gdk.pixbuf_new_from_file(app_theme.get_theme_file_path("image/toolbar_delete.png"))
        self.refresh_btn_pixbuf = gtk.gdk.pixbuf_new_from_file(app_theme.get_theme_file_path("image/toolbar_refresh.png"))
        
        self.skin_preview_pixbuf = app_theme.get_pixbuf("frame.png")
        self.toolbar_bg_pixbuf = app_theme.get_pixbuf("bar.png")
        self.cache_toolbar_bg_pixbuf = CachePixbuf()
        
    def __init_data(self):
        self.classified_items = {}
        rows = db.get_all()

        for row in rows:
            app_name = row[MESSAGE].app_name
            self.classified_items.setdefault(app_name, []).append(row)
        
            
    def refresh_view(self):
        self.__init_data()
        if len(self.classified_items):
            self.add_treeview()        
            self.add_listview(self.get_items_from_treeview_highlight())        
        else:
            align = gtk.Alignment(0.5, 0.5, 0, 0)
            align.add(Label("(Empty)"))
            container_remove_all(self.treeview_box)
            container_remove_all(self.listview_box)
            self.listview_box.pack_start(align, True, True)
        self.main_view_box.show_all()
        self.add_toolbar()
        
        
    def on_main_view_box_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        cr.rectangle(*rect)
        cr.set_source_rgb(*STROKE_LINE_COLOR)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        
    def on_toolbar_expose_event(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        cr.set_source_rgb(*STROKE_LINE_COLOR)
        cr.rectangle(*rect)
        cr.stroke()
        
        self.cache_toolbar_bg_pixbuf.scale(self.toolbar_bg_pixbuf.get_pixbuf(), rect.width, rect.height)
        cr.set_source_pixbuf(self.cache_toolbar_bg_pixbuf.get_cache(), rect.x, rect.y)
        cr.paint()
        
    def on_treeview_draw_mask(self, cr, x, y, w, h):    
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()        
        draw_line(cr, (x+w-1, y), (x+w-1, y+h), "#b2b2b2")
        
    def on_treeview_click_item(self, widget, item, column, x, y):    
        if not item.is_parent:
            widget.set_highlight_item(item)
            
            self.add_listview(self.get_items_from_treeview_highlight())
            
    def on_treeview_double_click_item(self, widget, item, column, x, y):
        if item.is_parent:
            if item.is_expand:
                item.unexpand()
            else:
                item.expand()
            
    def on_treeview_right_press_items(self, widget, root_x, root_y, current_item, select_items):
        '''
        docs
        '''
        self.treeview.set_highlight_item(current_item)
        if not current_item.is_parent:
            def on_add_to_bl():
                blacklist.add(current_item.title)
                current_item.is_in_blacklist = True
                current_item.emit_redraw_request()
            def on_remove_from_bl():
                blacklist.remove(current_item.title)
                current_item.is_in_blacklist = False
                current_item.emit_redraw_request()
            
            menu_items = []
            if current_item.title in blacklist.bl:
                menu_items.append((None, "Remove from Blacklist", on_remove_from_bl))
            else:
                menu_items.append((None, "Add to Blacklist", on_add_to_bl))
    
            Menu(menu_items, True).show((int(root_x), int(root_y)))
        
                
    def add_treeview(self):
        
        categories = self.classified_items.keys()
        # root eles
        root_ele_software = TreeViewItem("Software Messages", True)
        root_ele_system = TreeViewItem("System Message", True)
        self.treeview = TreeView([root_ele_software, root_ele_system], expand_column=0)
        
        # add child items , CAN'T add_child_items before treeview constructed
        software_children = []
        system_children = []
        for category in categories:
            treeview_item = TreeViewItem(category)
            if category in blacklist.bl:
                treeview_item.is_in_blacklist = True
                
            category_first_message_hints = self.classified_items[category][0][MESSAGE]["hints"]
            if category_first_message_hints.has_key("desktop-entry"):
                desktop_file = category_first_message_hints["desktop-entry"] 
                if "System" in xdg.DesktopEntry(desktop_file).get("Categories"):
                    system_children.append(treeview_item)
            else:
                software_children.append(treeview_item)
        
        root_ele_software.add_child_items(software_children)        
        self.treeview.draw_mask = self.on_treeview_draw_mask
        
        self.treeview.set_highlight_item(software_children[0])
        self.treeview.set_size_request(220, -1)
        self.treeview.connect("single-click-item", self.on_treeview_click_item)
        self.treeview.connect("right-press-items", self.on_treeview_right_press_items)
        self.treeview.connect("double-click-item", self.on_treeview_double_click_item)

        
        container_remove_all(self.treeview_box)
        self.treeview_box.pack_start(self.treeview, True, True)
        self.treeview_box.show_all()
        
    def add_listview(self, items):
        '''
        docs
        '''
        container_remove_all(self.listview_box)
        
        if len(items) != 0:
            self.factory = ListviewFactory(items, "detail")
            self.listview = self.factory.listview
            
            self.listview_box.pack_start(self.listview)
            
        self.listview_box.show_all()
        
        
    def get_items_from_treeview_highlight(self):
        '''
        docs
        '''
        app_name = self.treeview.get_highlight_item().get_title()
        return self.classified_items[app_name]
    
    
    def add_titlebar(self, 
                     button_mask=["theme", "min", "max", "close"],
                     icon_path=app_theme.get_theme_file_path("image/icon_little.png"),
                     app_name="Message Manager", 
                     title=None, 
                     add_separator=False, 
                     show_title=True, 
                     enable_gaussian=True, 
                     ):

        # Init titlebar.
        self.titlebar = Titlebar(button_mask, 
                                 icon_path, 
                                 app_name, 
                                 title, 
                                 add_separator, 
                                 show_title=show_title, 
                                 enable_gaussian=enable_gaussian,
                                 )

        self.titlebar.theme_button.connect("clicked", self.theme_callback)
        self.titlebar.max_button.connect("clicked", lambda w: self.toggle_max_window())
        self.titlebar.min_button.connect("clicked", lambda w: self.min_window())
        self.titlebar.close_button.connect("clicked", self.close_callback)
        
        if self.resizable:
            self.add_toggle_event(self.titlebar)
        self.add_move_event(self.titlebar)

        self.titlebar_box.add(self.titlebar)
        
    def theme_callback(self, widget):
        print "theme_callback"
        skin_window = SkinWindow(self.skin_preview_pixbuf)
        skin_window.show_all()
        place_center(self, skin_window)

        return False
        
        
    def add_toolbar(self):
        
        toolbar_btn_box = gtk.HBox()
        toolbar_btn_box_align = gtk.Alignment(0.5, 0.5, 0, 0)
        
        import_btn = ToolbarItem(self.import_btn_pixbuf, "Import")
        import_btn.connect("clicked", self.on_toolbar_import_clicked)
        export_btn = ToolbarItem(self.export_btn_pixbuf, "Export")
        export_btn.connect("clicked", self.on_toolbar_export_clicked)
        delete_btn = ToolbarItem(self.delete_btn_pixbuf, "Delete")
        delete_btn.connect("clicked", self.on_toolbar_delete_clicked)
        refresh_btn = ToolbarItem(self.refresh_btn_pixbuf, "Refresh")
        refresh_btn.connect("clicked", self.on_toolbar_refresh_clicked)
        
        toolbar_btn_box.pack_start(import_btn, False, False, 2)
        toolbar_btn_box.pack_start(export_btn, False, False, 2)
        toolbar_btn_box.pack_start(delete_btn, False, False, 2)
        toolbar_btn_box.pack_start(refresh_btn, False, False, 2)
        toolbar_btn_box_align.add(toolbar_btn_box)

        look_in_Label = Label("Look in")
        
        self.category_comb = ComboBox([(item, index) for index, item in enumerate(self.classified_items)])
 

        self.time_comb = ComboBox([("Today", 0), 
                              ("Last week", 1), 
                              ("Latest month", 2),
                              ("The last three months", 3),
                              ("The recent year", 4),
                              ("All", 5)
                              ])
        self.category_comb.set_size_request(-1, TOOLBAR_ENTRY_HEIGHT)
        self.time_comb.set_size_request(-1, TOOLBAR_ENTRY_HEIGHT)
        combos_box = gtk.HBox()
        combos_box.pack_start(self.category_comb, False, False, 5)
        combos_box.pack_start(self.time_comb, False, False)
        
        combos_box_align = gtk.Alignment(0.5, 0.5, 1, 1)
        padding_height = (TOOLBAR_HEIGHT - TOOLBAR_ENTRY_HEIGHT) / 2 
        combos_box_align.set_padding(padding_height, padding_height, 5, 5)
        combos_box_align.add(combos_box)

        
        find_content_Label = Label("Find Content")
        

        search_entry = SearchEntry("Search")
        search_entry.connect("action-active", self.on_search_entry_action_active)
        search_entry_align = gtk.Alignment(0.5, 0.5, 1, 1)
        search_entry_align.set_padding(padding_height, padding_height, 5, 5)
        search_entry_align.add(search_entry)
        
        #Align left
        self.toolbar_box.pack_start(toolbar_btn_box_align, False, False, 5)

        #Align right
        self.toolbar_box.pack_end(search_entry_align, False, True, 5)
        self.toolbar_box.pack_end(find_content_Label, False, False, 5)
        self.toolbar_box.pack_end(combos_box_align, False, False, 0) 
        self.toolbar_box.pack_end(look_in_Label, False, False, 5)       
        self.toolbar_box.pack_end(ToolbarSep(), False, False, 5)        
        
        
    def get_search_result_iter(self, search_str):
        search_category = self.category_comb.get_current_item()[0]
        search_timedelta = timedelta_dict[self.time_comb.get_current_item()[0]]
        
        total_search_result = []
        
        # self.classified_items don't have the key "All", but i can't added it in __init_data,
        # otherwise, it will have some bad effect on treeview left.
        if search_category != "All":
            items_should_search_in = self.classified_items[search_category]
        else:
            items_should_search_in = list(self.classified_items.itervalues())
        
        for item in items_should_search_in:
            item_datetime = datetime.strptime(item.time, "%Y/%m/%d-%H:%M:%S")
            if datetime.today() - item_datetime < search_timedelta:
                total_search_result.append(item)
                
        for item in total_search_result:
            item_message = item.message
            if item_message.body.find(search_str) != -1:
                yield item
            
    def on_search_entry_action_active(self, widget, text):
        search_result_iter = self.get_search_result_iter(text)
        
        self.add_listview(list(search_result_iter))
        
    def on_toolbar_import_clicked(self, widget):
        filename_to_import = ""
        def ok_clicked(filename):
            filename_to_import = filename
            
        def cancel_clicked():
            self.update_status_bar("Import cancelled.")
            
        OpenFileDialog("File To Import:", self, ok_clicked, None)
        
        if not len(filename_to_import):
            print "filename_to_import"
            try:
                db.import_db(filename_to_import)
            except Exception, e:
                print "exception"
                self.update_status_bar("Import failed, wrong file type!")
            else:
                print "else"
                self.update_status_bar("Import finished, congratulations!")        
        
    def on_toolbar_export_clicked(self, widget):
        
        def ok_clicked(filename):
            db.export_db(filename)
            self.update_status_bar("Export Succeed!!!")
            
        def cancel_clicked():
            self.update_status_bar("Export cancelled!")
            
        SaveFileDialog("File To Export:", self, ok_clicked, None)
        
        
    def on_toolbar_delete_clicked(self, widget):
        def on_ok_clicked():
            for row in self.listview.select_rows:
                db.remove(self.listview.visible_items[row].time)
                
            self.listview.delete_items([self.listview.visible_items[row] for row in self.listview.select_rows])            
            self.update_status_bar("Deteted!")
                
        dialog = ConfirmDialog(
                "Delete skin",
                "Are you sure delete selected items?",
                confirm_callback = on_ok_clicked)
        dialog.show_all()
        
        
    def on_toolbar_refresh_clicked(self, widget):
        self.refresh_view()
        
        self.update_status_bar("View has been refreshed!")
        
        
    def update_status_bar(self, message):
        def pop_message():
            self.status_bar.set_text("")
            
        self.status_bar.set_text(message)
        gobject.timeout_add(3000, pop_message)
            
    
    def close_callback(self, widget):
        '''
        docs
        '''
        self.destroy()