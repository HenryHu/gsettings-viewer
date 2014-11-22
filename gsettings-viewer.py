#!/usr/bin/env python

from gi.repository import Gtk
import subprocess
import os

def get_cmd_output_list(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, err = proc.communicate()
    ret = output.split('\n')
    if ret[-1:] == ['']:
        return ret[:-1]
    else:
        return ret

def get_cmd_ret(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, err = proc.communicate()
    return output.strip()

class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="GSettings viewer")

        self.set_size_request(800, 600)

        self.content = Gtk.HBox()
        self.add(self.content)

        renderer = Gtk.CellRendererText()

        self.schema_store = Gtk.TreeStore(str, bool)
        self.schema = Gtk.TreeView(self.schema_store)
        self.schema.get_selection().connect("changed", self.on_schema_selection_changed)

        self.key_list_store = Gtk.ListStore(str, str, str)
        self.key_list = Gtk.TreeView(self.key_list_store)
#        self.key_list.get_selection().connect("changed", self.on_key_selection_changed)

        schema_column = Gtk.TreeViewColumn("Schema", renderer, text=0)
        self.schema.append_column(schema_column)
        key_column = Gtk.TreeViewColumn("Key", renderer, text=0)
        self.key_list.append_column(key_column)
        value_column = Gtk.TreeViewColumn("Value", renderer, text=1)
        self.key_list.append_column(value_column)
        range_column = Gtk.TreeViewColumn("Range", renderer, text=2)
        self.key_list.append_column(range_column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.schema)
        self.content.add(scroll)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.key_list)
        self.content.add(scroll)
        self.connect("delete-event", Gtk.main_quit)

        self.preload = False
        self.cur_schema_name = None
        self.fill_schemas()

    def fill_schemas(self):
        model = self.schema_store

        schemas = get_cmd_output_list("gsettings list-schemas | sort")
        model.clear()
        for schema in schemas:
            model.append(None, [schema, self.preload])
        if self.preload:
            iter_ = model.get_iter_first()
            while iter_ is not None:
                self.fill_sub_schemas(model[iter_][0], model, iter_)
                iter_ = model.iter_next(iter_)

    def fill_keys(self, schema_name):
        keys = get_cmd_output_list("gsettings list-keys %s" % schema_name)
#        print "clearing"
        self.key_list_store.clear()
#        print "cleared"
        for key in keys:
            if not key:
                continue
#            print "key appended: %s" % key
            value = self.get_value(key)
            range_ = self.get_range(key)
            self.key_list_store.append([key, value, range_])

    def on_schema_selection_changed(self, selection):
        model, iter_ = selection.get_selected()
        if iter_ is not None:
            schema_name = model[iter_][0]
            schema_full_name = self.get_full_name(model, iter_)
            self.cur_schema_name = schema_full_name
#            print "calling fill_keys"
            self.fill_keys(schema_full_name)
            if not model[iter_][1]:
                self.fill_sub_schemas(schema_full_name, model, iter_)
                model[iter_][1] = True

    def get_value(self, key):
        return get_cmd_ret("gsettings get %s %s" % (self.cur_schema_name, key))

    def get_range(self, key):
        return get_cmd_ret("gsettings range %s %s" % (self.cur_schema_name, key))

    def on_key_selection_changed(self, selection):
        model, iter_ = selection.get_selected()
#        print model, iter_, selection.count_selected_rows()
        if iter_ is not None:
            key_name = model[iter_][0]
            os.system("gsettings get %s %s" % (self.cur_schema_name, key_name))

    def fill_sub_schemas(self, schema_full_name, model, iter_):
        children = get_cmd_output_list("gsettings list-children %s" % schema_full_name)
        for child in children:
            (name, fullpath) = child.split(None)
            model.insert_after(iter_, None, [name, False])

    def get_full_name(self, model, iter_):
        name = model[iter_][0]
        while iter_ is not None:
            parent = model.iter_parent(iter_)
            if parent is None:
                break
            name = model[parent][0] + "." + name
            iter_ = parent
        return name


win = MyWindow()

win.show_all()

Gtk.main()
