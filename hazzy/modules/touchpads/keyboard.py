#!/usr/bin/env python

#   Popup keyboard emulator for use on all alphanumeric entries

#   Copyright (c) 2017 Kurt Jacobson
#        <kcjengr@gmail.com>
#
#   This file is part of Hazzy.
#
#   Hazzy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Hazzy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Hazzy.  If not, see <http://www.gnu.org/licenses/>.

import pygtk
import gtk
import os
import sys
import gobject
import logging

log = logging.getLogger("HAZZY.KEYBOARD")

pydir = os.path.abspath(os.path.dirname(__file__))
IMAGEDIR = os.path.join(pydir, "ui")

_keymap = gtk.gdk.keymap_get_default()

def singleton(cls):
    return cls()

@singleton
class Keyboard():

    def __init__(self):

        self.entry = None
        self.parent = None
        self.persistent = False

        # Glade setup
        gladefile = os.path.join(IMAGEDIR, 'keyboard.glade')

        self.builder = gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")

        self.wait_counter = 0

        self.window.set_keep_above(True)

        self.letters = 'abcdefghijklmnopqrstuvwxyz ' # Now I've said my abc's
#                Don't remove the space character ^ It's named ' ' in glade too!

        self.numbers = '`1234567890-=' # Now I've said my 1 2 3's

        # Relate special character to their glade names.
        self.characters = {'`':'~', '1':'!', '2':'@', '3':'#', '4':'$',
                           '5':'%', '6':'^', '7':'&', '8':'*', '9':'(',
                           '0':')', '-':'_', '=':'+', '[':'{', ']':'}',
                           '\\':'|', ';':':', "'":'"', ',':'<', '.':'>',
                           '/':'?'} # Now I've said my @#$%^%!

        self.letter_btn_dict = dict((l, self.builder.get_object(l)) for l in self.letters)

        self.number_btn_dict = dict((n, self.builder.get_object(n)) for n in self.characters)

        # Connect letter button press events
        for l, btn in self.letter_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)

        # Connect number button press events
        for l, btn in self.number_btn_dict.iteritems():
            btn.connect("pressed", self.emulate_key) #self.on_button_pressed)

# =========================================================
# Keyboard Settings
# =========================================================

    # Caps Lock
    def on_caps_lock_toggled(self, widget):
        if widget.get_active():
            self.caps(True)
        else:
            self.caps(False)

    # Left shift unshifts after keypress
    def on_left_shift_toggled(self, widget):
        if widget.get_active():
            self.shift(True)
        else:
            self.shift(False)

    # Right shift is "sticky"
    def on_right_shift_toggled(self, widget):
        if widget.get_active():
            self.shift(True)
        else:
            self.shift(False)

    # Caps lock action
    def caps(self, data = False):
        if data:
            for l, btn in self.letter_btn_dict.iteritems():
                btn.set_label(l.upper())
        else:
            for l, btn in self.letter_btn_dict.iteritems():
                btn.set_label(l.lower())

    # Shift action, inverts caps lock setting 
    def shift(self, data = False):
        if data:
            for n, btn in self.number_btn_dict.iteritems():
                btn.set_label(self.characters[n])
            if self.builder.get_object('caps_lock').get_active():
                self.caps(False)
            else:
                self.caps(True)
        else:
            for n, btn in self.number_btn_dict.iteritems():
                btn.set_label(n)
            if self.builder.get_object('caps_lock').get_active():
                self.caps(True)
            else:
                self.caps(False)

            self.builder.get_object('left_shift').set_active(False)


# =========================================================
# Keyboard Emulation
# =========================================================

    def emulate_key(self, widget, key=None):
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)

            if key:
                event.keyval = int(gtk.gdk.keyval_from_name(key))
            else:
                event.keyval = ord(widget.get_label())

            event.hardware_keycode = _keymap.get_entries_for_keyval(event.keyval)[0][0]

            # add control mask if ctrl is active
            if self.builder.get_object('ctrl').get_active():
                event.state = gtk.gdk.CONTROL_MASK
                self.builder.get_object('ctrl').set_active(False)

            event.window = self.entry.window
            self.entry.event(event)    # Do the initial event

            # Call key repeat function every 50ms
            self.wait_counter = 0      # Set counter for repeat timeout
            gobject.timeout_add(50, self.key_repeat, widget, event)

        except Exception as e:
            log.exception(e)
            #log.error("HAZZY KEYBOARD ERROR: key emulation error - " + str(e))
            self.window.hide()

        # Unshift if left shift is active, right shift is "sticky"
        if self.builder.get_object('left_shift').get_active():
            self.shift(False)


    def key_repeat(self, widget, event):
        if widget.get_state() == gtk.STATE_ACTIVE:
            # 250ms initial repeat delay
            if self.wait_counter < 5:
                self.wait_counter += 1
            else:
                try:
                    self.entry.event(event)    # Repeat the event
                except:
                    pass
            return True
        return False


# =========================================================
# Button Handlers
# =========================================================

    # Backspace
    def on_backspace_pressed(self, widget):
        self.emulate_key(widget, "BackSpace")

    # Tab
    def on_tab_pressed(self, widget):
        self.emulate_key(widget, "Tab")

    # Return
    def on_return_pressed(self, widget):
        self.enter(widget)

    # Escape
    def on_esc_pressed(self, widget, data=None):
        self.escape()

    # Left arrow
    def on_arrow_left_pressed(self, widget):
        self.emulate_key(widget, "Left")

    # Right arrow
    def on_arrow_right_pressed(self, widget):
        self.emulate_key(widget, "Right")

    # Up Arrow
    def on_arrow_up_pressed(self, widget):
        self.emulate_key(widget, "Up")

    # Down Arrow
    def on_arrow_down_pressed(self, widget):
        self.emulate_key(widget, "Down")

    # TODO add persistence mode on double click
    def on_ctrl_toggled(self, widget):
        pass

    # Catch real ESC or ENTER key presses
    def on_window_key_press_event(self, widget, event, data=None):
        kv = event.keyval
        if kv == gtk.keysyms.Escape:
            self.escape() # Close the keyboard
        elif kv == gtk.keysyms.Return or kv == gtk.keysyms.KP_Enter:
            self.enter(widget)
        else: # Pass other keypresses on to the entry widget
            #print _keymap.get_entries_for_keyval(kv)
            try:
                self.entry.emit("key-press-event", event)
            except:
                pass

    # Escape action
    def escape(self):
        try:
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = gtk.keysyms.Escape
            event.window = self.entry.window
            self.entry.event(event)
            self.entry.emit("key-press-event", event)
        except:
            pass
        self.window.hide()

    def enter(self, widget):
        self.emulate_key(widget, "Return")
        if not self.persistent:
            self.window.hide()

    def on_entry_loses_focus(self, widget, data=None):
        self.escape()

    def on_entry_key_press(self, widget, event, data=None):
        kv = event.keyval
        if kv == gtk.keysyms.Escape:
            self.window.hide() # Close the keyboard

# ==========================================================
# Show the keyboard
# ==========================================================

    def show(self, entry, persistent=False ):
        self.entry = entry
        self.persistent = persistent
        self.entry.connect('focus-out-event', self.on_entry_loses_focus)
        self.entry.connect('key-press-event', self.on_entry_key_press)
        if self.parent:
            pos = self.parent.get_position()
            self.window.move(pos[0]+105, pos[1]+440)
        self.window.show()

    def set_parent(self, parent):
        self.parent = parent


# ==========================================================
# For standalone testing
# ==========================================================

def show(widget, event):
    keyboard.show(entry)

def destroy(widget):
    gtk.main_quit()

def main():
    gtk.main()

if __name__ == "__main__":
    keyboard = Keyboard
    entry = gtk.Entry()
    window = gtk.Window()
    window.add(entry)
    window.connect('destroy', destroy)
    entry.connect('button-press-event', show)
    window.show_all()
    keyboard.show(entry)
    main()
