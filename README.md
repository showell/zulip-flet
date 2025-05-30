This is an experimental Zulip client written in flet.

It's in early stages as I write this (May 30, 2025), so all the normal warnings apply.

There are a couple goals here:

* I am learning how to use flet.
* I want a usable Zulip client that's easy for Python developers to hack on.
* I want a fairly re-usable data layer that's Pythonic.  I intend it for hacking as well, but I do eventually intend it to be something that certain folks can just "pull off the shelf" and use.

One nice thing about flet is that you avoid a lot of the coding headaches from the legacy Zulip client:
* no need for templates
* no need for CSS
* no need for jQuery
* much less action at a distance
* just no legacy in general (clean slate)

Everything about flet is pretty natural and Pythonic.  The entire UI paradigm is based on components.  You create components in a composable way.

Also, you have all the power of modern Python.  Async code just works very naturally, for example.

I use pydantic and dataclasses throughout the app, especially the data layer.

I also make the choice **not** to subclass flet components for now,
although I certainly won't rule that out forever.  Instead, I have
Python classes that wrap the flet controls.  Having said that, I 
am not religious about encapsulation, so certain container classes
may consume their children's controls directly, or, in some cases,
even manipulate them.  But I mostly try to have my own mechanisms
for coordinating between the components.

TODOS:
* add left sidebar code
* start to handle some live-update scenarios
* get mypy to play nice with flet
