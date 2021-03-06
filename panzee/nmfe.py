import os
import copy
import json


IMAGE_EXTS = (".png", ".jpg")


class Parser(object):
    """Parse a .scn file into a list of Command objects.
    This is not meant to be used directly; use Runtime.read instead.
    """
    def __init__(self, starting_cmd_index=0, starting_cmp_id=0, starting_tree_id=0):
        """Initalize a Parser object
        starting_cmd_index is the index this Parser should start at when assigning
        indexes to any generated Command objects - useful for scene support.
        starting_cmp_id and starting_tree_id are used for the same thing.
        """
        self._lines = []
        self._line_num = 0
        self._commands = []
        self._next_cmd_index = starting_cmd_index
        self._next_cmp_id = starting_cmp_id
        self._expecting_endif = False
        self._next_tree_id = starting_tree_id
        self._inside_tree = False
        self._playing_audio = False
        self._expecting_avatar = False

    def read(self, file_path):
        """Parse a file located at file_path
        Will raise a ParseException if a parsing error occurs.
        """
        self._lines = open(file_path).readlines()
        while self._lines:
            self._parse_next_line()

    def get_commands(self):
        """Get parsed commands in the form of a list
        """
        return self._commands

    def get_next_cmp_id(self):
        """Get next available comparison ID
        This function should not ordinarily be used save for new Command subclasses.
        """
        return self._next_cmp_id

    def get_next_tree_id(self):
        """Get next available decision tree ID
        """
        return self._next_tree_id

    def _read_next_line(self):
        line = self._lines.pop(0).strip("\n").lstrip(" ")
        self._line_num += 1
        return line

    def _parse_next_line(self):
        line = self._read_next_line()
        if not line:
            # early exit on empty line
            return
        # [ indicates a line with a command
        if line.startswith("["):
            delimiting_index = line.find("]")
            if delimiting_index == -1:
                raise ParseException('No delimiting "]" found on line %d' % self._line_num)
            if line.count("[") + line.count("]") > 2:
                raise ParseException("More than 2 brackets found on line %d" % self._line_num)
            # snip brackets, split arguments on word boundary
            args = line[1:delimiting_index].split()
            command_tag = args.pop(0)
            command = self._construct_command(command_tag, args)
            self._add_command(command)
        # multi-line dialogue statment
        elif line.startswith("~"):
            # remove initial ~
            dialogue = line[1:]
            while line.endswith("~") is False:
                try:
                    line = self._read_next_line()
                except IndexError:
                    raise ParseException('EOF reached while searching for delimiting "~"')
                # join with spaces so none have to be manually added by the writer
                dialogue = " ".join((dialogue, line))
            # remove final ~
            dialogue = dialogue[:-1]
            self._add_command(DialogueCommand(dialogue, self._line_num, self._next_cmd_index))
        # normal line, treat it as dialogue
        else:
            self._add_command(DialogueCommand(line, self._line_num, self._next_cmd_index))

    def _add_command(self, command):
        self._commands.append(command)
        self._next_cmd_index += 1

    def _construct_command(self, tag, args):
        handlers = {"actor" : self._construct_actor,
        "alias" : self._construct_alias,
        "set" : self._construct_set,
        "unset" : self._construct_unset,
        "if" : self._construct_if,
        "elseif" : self._construct_elseif,
        "else" : self._construct_else,
        "endif" : self._construct_endif,
        "tree" : self._construct_tree,
        "leaf" : self._construct_leaf,
        "endtree" : self._construct_endtree,
        "scene" : self._construct_scene,
        "audio" : self._construct_playaudio,
        "stopaudio" : self._construct_stopaudio,
        "background" : self._construct_background,
        "avatar" : self._construct_displayavatar,
        "exit" : self._construct_removeavatar,
        "position" : self._construct_avatarposition}
        if tag not in handlers.keys():
            raise ParseException('Unknown command "%s" found on line %d' % (tag, self._line_num))
        return handlers[tag](args)

    def _construct_actor(self, args):
        if len(args) > 1:
            raise ParseException("Unexpected arguments encountered on line %d" % self._line_num)
        self._expecting_avatar = True
        name = args[0]
        if name == "nobody":
            # remove the active speaker
            name = None
            self._expecting_avatar = False
        command = ActiveSpeakerCommand(name, self._line_num, self._next_cmd_index)
        return command

    def _construct_alias(self, args):
        if len(args) != 2:
            raise ParseException("Wrong number of arguments encountered on line %d" % self._line_num)
        alias, real_name = args[0], args[1]
        command = AddAliasCommand(alias, real_name, self._line_num, self._next_cmd_index)
        return command

    def _construct_set(self, args):
        self._check_arg_size(args, 1, 2)
        name = args[0]
        flag_val = None
        if len(args) > 1:
            flag_val = args[1]
            flag_val = autoconvert_flag_value(flag_val)
        command = SetFlagCommand(name, flag_val, self._line_num, self._next_cmd_index)
        return command

    def _construct_unset(self, args):
        self._check_arg_size(args, 1, 1)
        name = args[0]
        previous_unsets = search_for_command(self._commands, UnsetFlagCommand, _filter=lambda c: c.name == name)
        previous_sets = search_for_command(self._commands, SetFlagCommand,  _filter=lambda c: c.name == name)
        if not previous_sets:
            raise ParseException('Attempt to use "unset" statement on nonexistent flag made on line %d' % self._line_num)
        if previous_sets and previous_unsets:
            last_set = previous_sets[-1:][0]
            last_unset = previous_unsets[-1:][0]
            if last_set.index < last_unset.index:
                raise ParseException('Attempt to use "unset" statement on unset flag made on line %d' % self._line_num)
        command = UnsetFlagCommand(name, self._line_num, self._next_cmd_index)
        return command

    def _construct_if(self, args):
        self._check_arg_size(args, 1, 2)
        if self._expecting_endif is True:
            raise ParseException('Cannot nest "if" statements; attempt was made on line %d' % self._line_num)
        self._expecting_endif = True
        flag = args[0]
        value = None
        if len(args) > 1:
            value = args[1]
            value = autoconvert_flag_value(value)
        command = IfCommand(self._next_cmp_id, flag, value, self._line_num, self._next_cmd_index)
        return command

    def _construct_elseif(self, args):
        self._check_arg_size(args, 1, 2)
        if self._expecting_endif is False:
            raise ParseException('"elseif" statement found without matching "if" statement on line %d' % self._line_num)
        flag = args[0]
        value = None
        if len(args) > 1:
            value = args[1]
            value = autoconvert_flag_value(value)
        command = ElseifCommand(self._next_cmp_id, flag, value, self._line_num, self._next_cmd_index)
        return command

    def _construct_else(self, args):
        self._check_arg_size(args, 0, 0)
        if self._expecting_endif is False:
            raise ParseException('"else" statement found without matching "if" statement on line %d' % self._line_num)
        command = ElseCommand(self._next_cmp_id, self._line_num, self._next_cmd_index)
        return command

    def _construct_endif(self, args):
        self._check_arg_size(args, 0, 0)
        if self._expecting_endif is False:
            raise ParseException('"endif" statement found without matching "if" statement on line %d' % self._line_num)
        self._expecting_endif = False
        command = EndifCommand(self._next_cmp_id, self._line_num, self._next_cmd_index)
        self._next_cmp_id += 1
        return command

    def _construct_tree(self, args):
        self._check_arg_size(args, 1, 1)
        if self._inside_tree is True:
            raise ParseException('Attempt to nest "tree" statements made on line %d' % self._line_num)
        self._inside_tree = True
        flag_name = args[0]
        command = TreeCommand(self._next_tree_id, flag_name, self._line_num, self._next_cmd_index)
        return command

    def _construct_leaf(self, args):
        if len(args) == 0:
            raise ParseException('Attempt to use "leaf" statement without any text made on line %d' % self._line_num)
        if self._inside_tree is False:
            raise ParseException('Attempt to use "leaf" statement outside tree made on line %d' % self._line_num)
        text = " ".join(args)
        command = LeafCommand(self._next_tree_id, text, self._line_num, self._next_cmd_index)
        return command

    def _construct_endtree(self, args):
        self._check_arg_size(args, 0, 0)
        if self._inside_tree is False:
            raise ParseException('Attempt to use "endtree" statement outside of tree made on line %d' % self._line_num)
        self._inside_tree = False
        display_command = DisplayTreeCommand(self._next_tree_id, self._line_num, self._next_cmd_index)
        input_command = GetTreeInputCommand(self._next_tree_id, self._line_num, self._next_cmd_index)
        self._next_tree_id += 1
        # hacky fix to get around building two commands but having to return one
        self._add_command(display_command)
        return input_command

    def _construct_scene(self, args):
        self._check_arg_size(args, 1, float("inf"))
        self._add_command(SaveContextCommand(self._line_num, self._next_cmd_index))
        # handle spaces in scene file path
        scene_path = self._path_from_args(args) + '.scn'
        parser = Parser(self._next_cmd_index + 1, self._next_cmp_id + 1, self._next_tree_id + 1)
        parser.read(scene_path)
        for command in parser.get_commands():
            self._add_command(command)
        # _add_command takes care of incrementing the command index for us
        self._next_cmp_id = parser.get_next_cmp_id()
        self._next_tree_id = parser.get_next_tree_id()
        restore_context_command = RestoreContextCommand(self._line_num, self._next_cmd_index)
        return restore_context_command

    def _construct_playaudio(self, args):
        self._check_arg_size(args, 1, float("inf"))
        if self._playing_audio:
            raise ParseException("Attempt to play audio without stopping previous track made on line %d" % self._line_num)
        self._playing_audio = True
        audio_path = self._path_from_args(args)
        audio_command = PlayAudioCommand(audio_path, self._line_num, self._next_cmd_index)
        return audio_command

    def _construct_stopaudio(self, args):
        self._check_arg_size(args, 0, 0)
        if not self._playing_audio:
            raise ParseException("Attempt to stop audio without playing any made on line %d" % self._line_num)
        self._playing_audio = False
        audio_command = StopAudioCommand(self._line_num, self._next_cmd_index)
        return audio_command

    def _construct_background(self, args):
        self._check_arg_size(args, 1, 2)
        # backgrounds can't have spaces in their name
        background_path = args[0]
        if background_path == "none":
            background_path = None
        transition = None
        if len(args) > 1:
            transition = args[1]
        background_command = BackgroundCommand(background_path, transition, self._line_num, self._next_cmd_index)
        return background_command

    def _construct_displayavatar(self, args):
        self._check_arg_size(args, 1, 1)
        if self._expecting_avatar is False:
            raise ParseException("Attempt to use avatar before setting an actor made on line %d" % self._line_num)
        avatar = args[0]
        command = DisplayAvatarCommand(avatar, self._line_num, self._next_cmd_index)
        return command

    def _construct_removeavatar(self, args):
        self._check_arg_size(args, 0, 0)
        if self._expecting_avatar is False:
            raise ParseException("Attempt to remove avatar before setting an actor made on line %d" % self._line_num)
        self._expecting_avatar = False
        command = RemoveAvatarCommand(self._line_num, self._next_cmd_index)
        return command

    def _construct_avatarposition(self, args):
        self._check_arg_size(args, 1, 1)
        if self._expecting_avatar is False:
            raise ParseException("Attempt to set avatar positon before setting an actor made on line %d" % self._line_num)
        position = args[0]
        command = SetAvatarPositionCommand(position, self._line_num, self._next_cmd_index)
        return command

    def _check_arg_size(self, args, low_end, high_end):
        if len(args) > high_end:
            raise ParseException("Too many arguments encountered on line %d" % self._line_num)
        elif len(args) < low_end:
            raise ParseException("Too few arguments encountered on line %d" % self._line_num)

    def _path_from_args(self, args):
        return ' '.join(args)


class Runtime(object):
    """Provide runtime functionality for the NMF engine
    This is the main class that should be utilized by external code.
    """

    def __init__(self, view):
        """Initialize a Runtime object
        view is a class implementing most of the methods found in MockView,
        in test/test_nmfe.py. See bin/nmfe-player.py for two full implementations
        of a view.
        """
        self._index = 0
        self._commands = []
        self._contexts = {}
        self._view = view
        self._aliases = {}
        self._flags = {}
        self._root = ""

    def read(self, file_path):
        """Parse a file located at file_path
        Convenience wrapper around Parser.read that binds all incoming commands
        to this Runtime object.
        """
        parser = Parser()
        parser.read(file_path)
        self._commands = parser.get_commands()
        for command in self._commands:
            command.bind_to_runtime(self)
            command.bind_to_view(self._view)
        self._root = os.path.dirname(file_path)

    def can_step(self):
        """Return True if there are more commands to be executed, False otherwise
        """
        return self._index < len(self._commands)

    def step(self):
        """Executes next available command
        Call Runtime.can_step first to ensure this method will not throw
        an exception.
        """
        command = self._commands[self._index]
        self._save_context()
        self._index += 1
        return command

    def verify(self):
        """Verifies integrity of all loaded commands
        Some commands have data that cannot be verified at parse time, such as
        the existence/validity of media files. This function ensures all commands
        get a chance to verify things like that.
        """
        for command in self._commands:
            command.verify()

    def get_state(self):
        """Return runtime state in a form suitable for serialization
        """
        state = {}
        state["context"] = self.get_context()
        commands = state["context"]["cmds"]
        # convert command objects to their indexes
        # much easier to serialize this way; no pesky complex datatypes
        state["context"]["cmds"] = self._commands_to_indexes(commands)
        state["index"] = self._last_executed_index()
        return state

    def load_state(self, state):
        """Load from a previously-saved runtime state
        The format of the state variable is exactly the same that
        Runtime.get_state returns.
        """
        context = state["context"]
        command_indexes = state["context"]["cmds"]
        # convert index numbers to command objects
        # can't restore state based off a bunch of ints, can we?
        context_commands = self._indexes_to_commands(command_indexes)
        index = state["index"]
        self._partial_restore_context(context)
        self.jump_to(index)
        self._view.restore_context(context_commands)

    def jump_to(self, index):
        """Jump without context to the given index
        This method does not restore context, which is probably not what you
        want; it's normally wiser to use Runtime.jump_with_context instead.
        Additionally, this method does no checks to make sure whether the given
        index is in bounds - try to stick to using indexes directly from a
        Command object or from Runtime.search_for_command if you can help it.
        This method does not immediately execute the jumped-to index - be sure
        that you do this after calling this method..
        """
        self._index = index

    def jump_with_context(self, index):
        """Jump to the given index and restore context
        All the warnings listed in the documentation for Runtime.jump_to
        apply here.
        """
        context = self.get_context(index)
        context_commands = context["cmds"]
        self._partial_restore_context(context)
        self.jump_to(index)
        self._view.restore_context(context_commands)

    def add_alias(self, alias, real_name):
        """Add an alias for an actor
        """
        self._aliases[alias] = real_name

    def has_real_name_for(self, alias):
        """Return True if alias is registered, False otherwise.
        """
        return alias in self._aliases.keys()

    def get_name_for(self, alias):
        """Return the real name assigned to the given alias
        """
        return self._aliases[alias]

    def has_alias_for(self, name):
        """Return True if there is an alias assigned to name, False otherwise
        """
        inverted = {v: k for k, v in self._aliases.iteritems()}
        return name in inverted.keys()

    def get_alias_for(self, name):
        """Return the alias associated with name
        """
        inverted = {v: k for k, v in self._aliases.iteritems()}
        return inverted[name]

    def set_flag(self, name, value):
        """Set a flag
        The given value is automatically converted to an integer if value
        constitutes a valid integer in string form.
        """
        self._flags[name] = autoconvert_flag_value(value)

    def get_flag(self, name):
        """Return the value of the flag with the given name
        Raises KeyError if there is no such flag.
        """
        return self._flags[name]

    def unset_flag(self, name):
        """Remove the flag with the given name
        Raises KeyError if there is no such flag.
        """
        del self._flags[name]

    def has_flag(self, name):
        """Return True if a flag with the given name exists, False otherwise
        """
        return name in self._flags.keys()

    def search_for_command(self, cmd_class, start_range = None, end_range = None, _filter=lambda c: True):
        """Convenience wrapper around nmfe.search_for_command
        See that function for more documentation
        """
        return search_for_command(self._commands, cmd_class, start_range, end_range, _filter)

    def get_context(self, index = None):
        """Return the context of the given index
        if index is None, return the context for the last-executed index
        """
        if index:
            return self._contexts[index]
        else:
            return self._contexts[self._last_executed_index()]

    def restore_context(self, context):
        """Run commands necessary to restore the given context
        """
        self._partial_restore_context(context)
        context_commands = context["cmds"]
        self._view.restore_context(context_commands)

    def get_scene_root(self):
        """Return the root directory of the main scene file
        """
        return self._root

    def _save_context(self):
        commands = []
        command_types = []
        command_filters = {PlayAudioCommand : self._check_audio,
        StopAudioCommand : self._check_audio}
        # reversing the list causes the most recently-executed commmands to be considered first
        # useful since most recent = most relevant to context, which are the ones we want
        for candidate_cmd in reversed(self._commands[:self._index]):
            if candidate_cmd.save_with_context is True:
                _filter = lambda c, _: type(c) not in command_types
                if command_filters.has_key(type(candidate_cmd)):
                    _filter = command_filters[type(candidate_cmd)]
                if _filter(candidate_cmd, commands):
                    commands.append(candidate_cmd)
                    command_types.append(type(candidate_cmd))
                else:
                    continue
        self._contexts[self._index] = {"aliases" : copy.copy(self._aliases), "flags" : copy.copy(self._flags), "cmds" : commands}

    def _partial_restore_context(self, context):
        new_aliases = context["aliases"]
        new_flags = context["flags"]
        self._aliases = new_aliases
        self._flags = new_flags

    def _check_audio(self, candidate_cmd, commands):
        if type(candidate_cmd) is PlayAudioCommand:
            return StopAudioCommand not in commands
        if type(candidate_cmd) is StopAudioCommand:
            return PlayAudioCommand not in commands

    def _commands_to_indexes(self, commands):
        indexes = []
        for command in commands:
            indexes.append(command.index)
        return indexes

    def _indexes_to_commands(self, indexes):
        commands = []
        for index in indexes:
            command = self._commands[index]
            commands.append(command)
        return commands

    def _last_executed_index(self):
        return self._index - 1


class ParseException(Exception):
    pass


class VerifyException(Exception):
    pass


class RuntimeCommand(object):
    """Base class for Command objects
    Don't instantiate this class directly; inherit from it instead.
    """

    # can_stop_at is a flag to indicate to a view whether this command is a point
    # at which the view can save at or rewind to
    can_stop_at = False
    # if save_with_context is True, then by default the runtime will save
    # the most recent occurrence of this command when saving context
    # there are other methods of choosing which to save though,
    # see Runtime._save_context to see how
    save_with_context = False

    def __init__(self, line_num, index):
        self.runtime = None
        self.view = None
        self.line_num = line_num
        self.index = index

    def execute(self):
        """Execute command
        When ovverriding this method in a subclass, be sure to take into account
        the fact that this method could potentially be called multiple times
        due to the runtime rewinding to a previous point.
        """
        pass

    def verify(self):
        """Verify this command object's integrity
        When overriding this method in a subclass, throw VerifyException if
        verification fails, but do nothing otherwise.
        """
        pass

    def bind_to_runtime(self, runtime):
        self.runtime = runtime

    def bind_to_view(self, view):
        self.view = view


class DialogueCommand(RuntimeCommand):

    can_stop_at = True

    def __init__(self, dialogue, line_num, index):
        super(DialogueCommand, self).__init__(line_num, index)
        self._dialogue = dialogue

    def execute(self):
        self.view.display_dialogue(self._dialogue)


class ActiveSpeakerCommand(RuntimeCommand):

    save_with_context = True

    def __init__(self, name, line_num, index):
        super(ActiveSpeakerCommand, self).__init__(line_num, index)
        self._name = name

    def execute(self):
        name = self._name
        if self.runtime.has_real_name_for(name):
            name = self.runtime.get_name_for(name)
        self.view.set_speaker(name)


class AddAliasCommand(RuntimeCommand):

    def __init__(self, alias, real_name, line_num, index):
        super(AddAliasCommand, self).__init__(line_num, index)
        self._alias = alias
        self._real_name = real_name

    def execute(self):
        self.runtime.add_alias(self._alias, self._real_name)


class SetFlagCommand(RuntimeCommand):

    def __init__(self, name, value, line_num, index):
        super(SetFlagCommand, self).__init__(line_num, index)
        self.name = name
        self.value = value

    def execute(self):
        self.runtime.set_flag(self.name, self.value)


class UnsetFlagCommand(RuntimeCommand):

    def __init__(self, name, line_num, index):
        super(UnsetFlagCommand, self).__init__(line_num, index)
        self.name = name

    def execute(self):
        self.runtime.unset_flag(self.name)


class IfCommand(RuntimeCommand):

    def __init__(self, cmp_id, flag, cmp_val, line_num, index):
        super(IfCommand, self).__init__(line_num, index)
        self.cmp_id = cmp_id
        self.flag = flag
        self.cmp_val = cmp_val
        self.cmp_successful = False

    def execute(self):
        self._compare()
        if self.cmp_successful is False:
            for cmd_type in [ElseifCommand, ElseCommand, EndifCommand]:
                if self._attempt_jump_to(cmd_type):
                    return

    def _compare(self):
        # reset in case we're re-executing due to skipping backwards
        self.cmp_successful = False
        if self.cmp_val is None:
            # testing for flag existence
            if self.runtime.has_flag(self.flag):
                self.cmp_successful = True
        else:
            if self.runtime.get_flag(self.flag) == self.cmp_val:
                self.cmp_successful = True

    def _attempt_jump_to(self, cmd_type):
        jump_point = None
        candidate_jump_points = self.runtime.search_for_command(cmd_type, self.index)
        for command in candidate_jump_points:
            # "is not self" fixes infinite loops generated by an elseif jumping to itself
            # obviously breaking encapsulation here, but this is easier than the alternative
            if command.cmp_id == self.cmp_id and command is not self:
                jump_point = command.index
                break
        if jump_point is not None:
            self.runtime.jump_to(jump_point)
            return True
        else:
            return False


class ElseifCommand(IfCommand):

    def execute(self):
        if self._previous_cmp_succeeded():
            self._attempt_jump_to(EndifCommand)
        else:
            super(ElseifCommand, self).execute()

    def _previous_cmp_succeeded(self):
        candidate_ifs = self.runtime.search_for_command(IfCommand, end_range=self.index)
        if_statement = None
        for statement in candidate_ifs:
            if statement.cmp_id == self.cmp_id:
                if_statement = statement
                break
        if if_statement.cmp_successful is True:
            return True
        elseifs = self.runtime.search_for_command(ElseifCommand, if_statement.index, self.index - 1)
        for statement in elseifs:
            if statement.cmp_successful is True:
                return True
        return False


class ElseCommand(RuntimeCommand):

    def __init__(self, cmp_id, line_num, index):
        super(ElseCommand, self).__init__(line_num, index)
        self.cmp_id = cmp_id


class EndifCommand(RuntimeCommand):

    def __init__(self, cmp_id, line_num, index):
        super(EndifCommand, self).__init__(line_num, index)
        self.cmp_id = cmp_id


class TreeCommand(RuntimeCommand):

    can_stop_at = True

    def __init__(self, tree_id, flag_name, line_num, index):
        super(TreeCommand, self).__init__(line_num, index)
        self.tree_id = tree_id
        self.flag_name = flag_name


class LeafCommand(RuntimeCommand):

    def __init__(self, tree_id, choice_text, line_num, index):
        super(LeafCommand, self).__init__(line_num, index)
        self.tree_id = tree_id
        self.choice_text = choice_text


class DisplayTreeCommand(RuntimeCommand):

    def __init__(self, tree_id, line_num, index):
        super(DisplayTreeCommand, self).__init__(line_num, index)
        self.tree_id = tree_id

    def execute(self):
        choices = self._collect_choices()
        self.view.display_choices(choices)

    def _collect_choices(self):
        candidate_choice_cmds = self.runtime.search_for_command(LeafCommand, end_range=self.index)
        choices = []
        for command in candidate_choice_cmds:
            if command.tree_id == self.tree_id:
                choice_text = command.choice_text
                choices.append(choice_text)
        return choices


class GetTreeInputCommand(RuntimeCommand):

    def __init__(self, tree_id, line_num, index):
        super(GetTreeInputCommand, self).__init__(line_num, index)
        self.tree_id = tree_id

    def execute(self):
        flag_name = self._get_flag_name()
        choice = self.view.get_selected_choice()
        self.runtime.set_flag(flag_name, choice)

    def _get_flag_name(self):
        tree = self.runtime.search_for_command(TreeCommand, end_range=self.index)[0]
        return tree.flag_name


class SaveContextCommand(RuntimeCommand):
    # stub class, used as a marker when determining where to restore context after a scene
    pass


class RestoreContextCommand(RuntimeCommand):
    """Restores context after a scene transition
    """

    def execute(self):
        last_save = self._most_recent_save_context()
        index = last_save.index
        old_context = self.runtime.get_context(index)
        current_context = self.runtime.get_context(self.index)
        # merge contexts so as to save new aliases and flag values, but keep
        # old actor information
        merged_context = self._merge_contexts(old_context, current_context)
        self.runtime.restore_context(merged_context)

    def _most_recent_save_context(self):
        candidates = self.runtime.search_for_command(SaveContextCommand, end_range=self.index)
        return candidates[-1]

    def _merge_contexts(self, old_context, new_context):
        merged_context = old_context.copy()
        merged_context["aliases"].update(new_context["aliases"])
        merged_context["flags"].update(new_context["flags"])
        return merged_context


class PlayAudioCommand(RuntimeCommand):

    save_with_context = True
    AUDIO_DIR = "assets/audio"
    AUDIO_EXTS = (".mp3", ".ogg", ".wav")

    def __init__(self, audio_path, line_num, index):
        super(PlayAudioCommand, self).__init__(line_num, index)
        self.audio_path = audio_path

    def execute(self):
        path = self._find_audio_path()
        self.view.play_audio(path)

    def _find_audio_path(self):
        base_path = os.path.join(self.runtime.get_scene_root(), PlayAudioCommand.AUDIO_DIR, self.audio_path)
        path = None
        for extension in PlayAudioCommand.AUDIO_EXTS:
            candidate_path = base_path + extension
            if os.path.exists(candidate_path):
                path = candidate_path
                break
        return path


class StopAudioCommand(RuntimeCommand):

    save_with_context = True

    def execute(self):
        self.view.stop_audio()


class BackgroundCommand(RuntimeCommand):

    save_with_context = True
    BACKGROUND_DIR = os.path.join("assets", "backgrounds")

    def __init__(self, background_path, transition, line_num, index):
        super(BackgroundCommand, self).__init__(line_num, index)
        self.background_path = background_path
        self.transition = transition

    def execute(self):
        if self.background_path is None:
            self.view.clear_background()
        else:
            path = self._get_path_to_background()
            self.view.display_background(path, self.transition)

    def verify(self):
        if self.background_path is not None and self._get_path_to_background() is None:
            raise VerifyException("Attempt to use non-existent background encountered on line %d" % self.line_num)

    def _get_path_to_background(self):
        base_path = os.path.join(self.runtime.get_scene_root(), BackgroundCommand.BACKGROUND_DIR, self.background_path)
        path = None
        for extension in IMAGE_EXTS:
            candidate_path = base_path + extension
            if os.path.exists(candidate_path):
                path = candidate_path
                break
        return path


#TODO: write test cases for avatar commands
class AvatarCommand(RuntimeCommand):

    def _get_name(self, use_alias=True):
        name = self.view.get_speaker()
        if use_alias and self.runtime.has_alias_for(name):
            name = self.runtime.get_alias_for(name)
        return name


class DisplayAvatarCommand(AvatarCommand):

    save_with_context = True
    AVATAR_DIR = os.path.join("assets", "avatars")

    def __init__(self, avatar, line_num, index):
        super(DisplayAvatarCommand, self).__init__(line_num, index)
        self.avatar = avatar

    def execute(self):
        avatar_path = self._get_path_to_avatar()
        self.view.display_avatar(avatar_path)

    def verify(self):
        if self._get_path_to_avatar() is None:
            raise VerifyException("Attempt to use non-existent avatar encountered on line %d" % self.line_num)

    def _get_path_to_avatar(self):
        name = self._get_name(use_alias=True)
        base_path = os.path.join(self.runtime.get_scene_root(), DisplayAvatarCommand.AVATAR_DIR, name, self.avatar)
        path = None
        for extension in IMAGE_EXTS:
            candidate_path = base_path + extension
            if os.path.exists(candidate_path):
                path = candidate_path
                break
        return path


class RemoveAvatarCommand(AvatarCommand):

    def execute(self):
        name = self._get_name(use_alias=False)
        self.view.remove_avatar(name)
        self.view.set_speaker(None)


class SetAvatarPositionCommand(AvatarCommand):

    def __init__(self, position, line_num, index):
        super(SetAvatarPositionCommand, self).__init__(line_num, index)
        self.position = position

    def execute(self):
        name = self._get_name(use_alias=False)
        self.view.set_avatar_position(name, self.position)


class WaitCommand(RuntimeCommand):

    def __init__(self, duration, line_num, index):
        super(WaitCommand, self).__init__
        self.duration = duration

    def execute(self):
        self.view.wait(duration)


def autoconvert_flag_value(value):
    if value == None:
        return value
    elif type(value) == int:
        return value
    elif value.isdigit():
        value = int(value)
    return value


def search_for_command(commands, cmd_class, start_range=None, end_range=None, _filter=lambda c: True):
    if end_range is None:
        cmd_slice = commands[start_range:]
    elif start_range is None:
        cmd_slice = commands
    else:
        cmd_slice = commands[start_range:-end_range]
    results = []
    for command in cmd_slice:
        if type(command) == cmd_class and _filter(command):
            results.append(command)
    return results


def state_to_serializable(state):
    return json.dumps(state)


def serializable_to_state(serializable):
    return json.loads(serializable)
