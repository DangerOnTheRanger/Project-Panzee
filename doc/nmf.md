Novel Markup Format
===================

The Novel Markup Format (NMF) is the markup system used to describe in-engine cutscenes
inside Project Panzee. As Project Panzee's story mode follows a similar flow and
level of interactability to that of the average visual novel - outside of battles,
at least - inspiration for NMF's syntax was taken from similar efforts made with
visual novel engines such as RenPy.


Dialogue
--------

The meat of any visual novel is the dialogue itself; thus, great care has been taken
in the NMF engine (NMFe) syntax to make the act of writing dialogue take as little actual markup as possible.
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

Actors are NMFe's method of attaching a speaker, or character, to dialogue.
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
is not included, as that is detected automatically by NMFe. Transitions can also
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
sprites representing various characters, as well. NMFe does this through
the use of what it calls avatars. Each actor can be assigned an avatar, which contains
info on what sprites constitute an actor's appearance, as well as its current position
on the screen. Avatars are defined in a separate folder, one for each actor. The name
of the folder is used to match the folder to the correct actor or alias.

An avatar folder looks like this:

    /
      neutral.png
      surprised.png
      sad.png
      happy.png

NMFe automatically finds and detects any image files in the avatar folder.
The names of those image files can then be referenced to change the avatar's appearance.

Here is an example of how avatars are used:

    Currently there are no avatars. Let's change that.
    But we'll need to define some actors first.
    [actor bubba]
    [position left]
    Avatars can be moved around the screen as well.
    By default, preset positions "left," "right," and "center" are available.
    A percentage-based system similar to CSS is also available, however.
    Transitions can also be used for moving avatars around.
    [position center slide]
    Like so.
    By default, only the slide transition is supported, though.
    Say you want to remove an avatar from the screen. What do you do?
    Why, use the exit command.
    [exit]
    Once the exit command is used, the actor is unset as well.


Audio
-----

NMFe has basic support for background audio, which is utilized with the `[audio]`
command, as in the following example.

    Currently, no audio is playing.
    But, we can change that.
    [audio jazz]
    Just like with avatars, NMFe automatically detects filename extensions.
    We can stop audio as well, with the stopaudio command.
    [stopaudio]
    Now, no audio is playing.


Scenes
------

It is very impractical to write an entire visual novel in a single file, so NMFe
supports *scenes* - which, as the term implies, allows a writer to break up the entire
story into separate standalone files. For instance, say we have a scene named `lake.scn`:


    [background lake]
    A peaceful lake.
    Some birds can be seen swooping low over the water's surface.

And then, a scene named `trip.scn`:

    [background house]
    [actor daisy]
    Hey, why don't we go to the lake?
    [scene lake]
    That was a fun trip!

NMFe automatically remembers context when switching scenes. Active actors,
backgrounds, and so on are automatically preserved when returning from a scene.


Flags and Decision-Making
-------------------------

NMFe supports *flags*, which are essentially repurposed variables used to remember
the outcome of a prior choice made by the player. Basic `if/then`-esque decision-making
based on flags is also supported, including testing the existence and value of a given flag.

An example of how to use both flags and decision-making:

    Flags are set with the set command. Let's set one now.
    [set test_flag 1]
    Flags can have number and string values, though the same flag cannot contain multiple types.
    [if test_flag]
    This dialogue will display, since we're only testing for existence here.
    [endif]
    [if test_flag 2]
    This dialogue will never display; test_flag contains 1, not 2.
    [elseif test_flag 1]
    This dialogue will display; test_flag contains the correct value.
    [else]
    This dialogue will not display; a prior condition was met.
    [endif]
    We can unset flags as well.
    [unset test_flag]


Decision Trees
--------------

NMFe also supports player-selected choices called decision trees, which go hand-in-hand with
the flags and `if/then` sequences discussed earlier.

    Decision trees are used with the tree command.
    We must give the name of a flag to pass the result of the decision tree into.
    Which choice will you pick?
    [tree choice]
    [leaf The first choice.]
    [leaf The second choice.]
    [leaf The third choice.]
    [endtree]
    [if choice 1]
    You picked the first choice.
    [elseif choice 2]
    You picked the second choice.
    [else]
    You picked the third choice.
    [endif]

As an interesting sidenote, it is perfectly valid to use `[if]` and other statements
inside a `[tree]` declaration, meaning it's possible to create different choices based
on the status of flags.


Delaying execution
------------------

Normally, NMF commands are executed as soon as possible, though sometimes it
is convenient to delay execution of later commands by some time; for instance,
to show a character's avatar going through a range of emotions. This is accomplished
through the `[wait]` command:

  This line displays instantly, but...
  [wait 2.5]
  This line will display a short time later. About 2.5 seconds later.
