import copy


class Parser(object):
    def __init__(self, starting_cmd_index=0, starting_cmp_id=0, starting_tree_id=0):
        self._lines = []
        self._line_num = 0
        self._commands = []
        self._next_cmd_index = starting_cmd_index
        self._next_cmp_id = starting_cmp_id
        self._expecting_endif = False
        self._next_tree_id = starting_tree_id
        self._inside_tree = False

    def read(self, file_path):
        self._lines = open(file_path).readlines()
        while self._lines:
            self._parse_next_line()

    def get_commands(self):
        return self._commands

    def get_next_cmp_id(self):
        return self._next_cmp_id

    def get_next_tree_id(self):
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
        elif line.startswith("~"):
            # remove initial ~
            dialogue = line[1:]
            while line.endswith("~") is False:
                line = self._read_next_line()
                # TODO: properly check for EOF
                # join with spaces so none have to be manually added by the writer
                dialogue = " ".join((dialogue, line))
            # remove final ~
            dialogue = dialogue[:-1]
            self._add_command(DialogueCommand(dialogue, self._line_num, self._next_cmd_index))
        else:
            self._add_command(DialogueCommand(line, self._line_num, self._next_cmd_index))

    def _add_command(self, command):
        self._commands.append(command)
        self._next_cmd_index += 1

    def _construct_command(self, tag, args):
        handlers = {'actor' : self._construct_actor,
        'alias' : self._construct_alias,
        'set' : self._construct_set,
        'unset' : self._construct_unset,
        'if' : self._construct_if,
        'elseif' : self._construct_elseif,
        'else' : self._construct_else,
        'endif' : self._construct_endif,
        'tree' : self._construct_tree,
        'leaf' : self._construct_leaf,
        'endtree' : self._construct_endtree,
        'scene' : self._construct_scene}
        if tag not in handlers.keys():
            raise ParseException('Unknown command "%s" found on line %d' % (tag, self._line_num))
        return handlers[tag](args)

    def _construct_actor(self, args):
        if len(args) > 1:
            raise ParseException("Unexpected arguments encountered on line %d" % self._line_num)
        name = args[0]
        if name == "nobody":
            # remove the active speaker
            name = None
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
        scene_path = ' '.join(args) + '.scn'
        parser = Parser(self._next_cmd_index + 1, self._next_cmp_id + 1, self._next_tree_id + 1)
        parser.read(scene_path)
        for command in parser.get_commands():
            self._add_command(command)
        # _add_command takes care of incrementing the command index for us
        self._next_cmp_id = parser.get_next_cmp_id()
        self._next_tree_id = parser.get_next_tree_id()
        restore_context_command = RestoreContextCommand(self._line_num, self._next_cmd_index)
        return restore_context_command

    def _check_arg_size(self, args, low_end, high_end):
        if len(args) > high_end:
            raise ParseException("Too many arguments encountered on line %d" % self._line_num)
        elif len(args) < low_end:
            raise ParseException("Too few arguments encountered on line %d" % self._line_num)


class Runtime(object):

    def __init__(self, view):
        self._index = 0
        self._commands = []
        self._contexts = {}
        self._next_cmd_index = 0
        self._line_num = 0
        self._lines = []
        self._view = view
        self._aliases = {}
        self._flags = {}
        self._next_cmp_id = 0
        self._expecting_endif = False
        self._next_tree_id = 0
        self._inside_tree = False

    def read(self, file_path):
        parser = Parser()
        parser.read(file_path)
        self._commands = parser.get_commands()
        for command in self._commands:
            command.bind_to_runtime(self)
            command.bind_to_view(self._view)

    def step(self):
        command = self._commands[self._index]
        self._save_context()
        self._index += 1
        return command

    def verify(self):
        for command in self._commands:
            command.verify()

    def jump_to(self, index):
        self._index = index

    def jump_with_context(self, index):
        context = self.get_context(index)
        context_commands = context["cmds"]
        self._partial_restore_context(context)
        self.jump_to(index)
        self._view.restore_context(context_commands)

    def add_alias(self, alias, real_name):
        self._aliases[alias] = real_name

    def has_alias_for(self, alias):
        return alias in self._aliases.keys()

    def get_alias_for(self, alias):
        return self._aliases[alias]

    def set_flag(self, name, value):
        self._flags[name] = autoconvert_flag_value(value)

    def get_flag(self, name):
        return self._flags[name]

    def unset_flag(self, name):
        del self._flags[name]

    def has_flag(self, name):
        return name in self._flags.keys()

    def search_for_command(self, cmd_class, start_range = None, end_range = None, _filter=lambda c: True):
        return search_for_command(self._commands, cmd_class, start_range, end_range, _filter)

    def get_context(self, index = None):
        if index:
            return self._contexts[index]
        else:
            return self._contexts[self._index]

    def restore_context(self, context):
        self._partial_restore_context(context)
        context_commands = context["cmds"]
        self._view.restore_context(context_commands)

    def _save_context(self):
        commands = {}
        # reversing the list causes the most recently-executed commmands to be considered first
        # useful since most recent = most relevant to context, which are the ones we want
        for candidate_cmd in reversed(self._commands[:self._index]):
            if candidate_cmd.save_with_context is True:
                if type(candidate_cmd) not in commands.keys():
                    commands[type(candidate_cmd)] = candidate_cmd
                else:
                    continue
        self._contexts[self._index] = {"aliases" : copy.copy(self._aliases), "flags" : copy.copy(self._flags), "cmds" : commands.values()}

    def _partial_restore_context(self, context):
        new_aliases = context["aliases"]
        new_flags = context["flags"]
        self._aliases = new_aliases
        self._flags = new_flags


class ParseException(Exception):
    pass


class VerifyException(Exception):
    pass


class RuntimeCommand(object):

    can_stop_at = False
    save_with_context = False

    def __init__(self, line_num, index):
        self.runtime = None
        self.view = None
        self.line_num = line_num
        self.index = index

    def execute(self):
        pass

    def verify(self):
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
        if self.runtime.has_alias_for(name):
            name = self.runtime.get_alias_for(name)
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

    def execute(self):
        last_save = self._most_recent_save_context()
        index = last_save.index
        context = self.runtime.get_context(index)
        self.runtime.restore_context(context)

    def _most_recent_save_context(self):
        candidates = self.runtime.search_for_command(SaveContextCommand, end_range=self.index)
        return candidates[-1]


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
