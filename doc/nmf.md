Novel Markup Format
===================

Novel Markup Format (NMF) is the markup system used to describe in-engine cutscenes
inside Project Panzee. As Project Panzee's story mode follows a similar flow and
level of interactability to that of the average visual novel - outside of battles,
at least - inspiration for NMF's syntax was taken from similar efforts made with
visual novel engines such as RenPy.


Dialogue
--------

The meat of any visual novel is the dialogue itself; thus, great care has been taken
in NMF to make the act of writing dialogue take as little actual markup as possible.
All raw lines of text that do not start with `[` are automatically counted as part of
the dialogue - for example:

    This will render as a single line of dialogue.
    This second line counts as a second, separate line of dialogue.
    The player has to hit Enter or a similar button to advance beyond each line.

If a line of dialogue is long enough that it would be better off broken up over several
lines of text in its NMF file, but should still be displayed all at once, the relevant
bits can be delimited with `~`, like so:

    ~All of this will render as a single line of dialogue. Even though this text
    is spread out over multiple lines, it will all render as a single line of dialogue -
    i.e, the player will not have to hit Enter to view this dialogue in its entirety.~


Actors
------

Actors are NMF's method of attaching a speaker, or character, to dialogue.
Actors can be specified with `[actor <name of actor>]`. Actors do not need to be declared
before they are used. For longer or unwieldy names, actors can be aliased with
`[alias <alias name> <name of actor>]`. It's also possible to clear the active actor with
the special line `[actor nobody]`. For example:

    This dialogue is spoken by nobody in particular.
    A perfect fit for narration.
    [actor Person 1]
    This dialogue is attributed to "Person 1."
    Note how we immediately started using the actor.
    [actor nobody]
    ~Now nobody is speaking again. Useful if you want to insert narration or something
    between spoken lines.~
    [alias teliel Teliel, Destroyer of Worlds]
    Now we're about to use an alias. You can declare these anywhere you'd like.
    You don't have to use them till you want to.
    [actor teliel]
    Like so.

Note that aliases cannot include spaces, though actor names can.


Backgrounds
-----------

Backgrounds are displayed with `[background <name of background>]`. The file extension
is not included, as that is detected automatically by the NMF engine. Transitions can also
be specified as an additional argument to the `background` command, such as
`[background <name of background> <transition type>]`. Valid transition types are:

* `fade-in`
* `zoom-out`

Background example:

    Currently the screen is black. No background can be seen.
    [background mountains fade-in]
    And with that, we just switched backgrounds.
    We can also remove backgrounds similar to actors.
    [background none]
    And now the screen is black again.


Avatars
-------

Most visual novel engines include support for not only backgrounds, but for foreground
sprites representing various characters, as well. Panzee's NMF engine does this through
the use of what it calls avatars. Each actor can be assigned an avatar, which contains
info on what sprites constitute an actor's appearance, as well as its current position
on the screen. Avatars are defined in a separate folder, one for each actor.

An avatar folder looks like this:

    /
      neutral.png
      surprised.png
      sad.png
      happy.png
      avatar.nav

The NMF engine automatically finds and detects any image files in the avatar folder.
The names of those image files can then be referenced to change the avatar's appearance. 
