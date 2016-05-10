import copy


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
        self._lines = open(file_path).readlines()
        while self._lines:
            self._parse_next_line()

    def step(self):
        command = self._commands[self._index]
        #TODO: support jumping forward with context past last executed command?
        self._save_context()
        self._index += 1
        return command

    def jump_to(self, index):
        self._index = index

    def jump_with_context(self, index):
        context_commands = self._get_context(index)["cmds"]
        self._partial_restore_context(index)
        self.jump_to(index)
        self._view.restore_context(context_commands)

    def add_alias(self, alias, real_name):
        self._aliases[alias] = real_name

    def has_alias_for(self, alias):
        return alias in self._aliases.keys()

    def get_alias_for(self, alias):
        return self._aliases[alias]

    def set_flag(self, name, value):
        self._flags[name] = self._autoconvert_flag_value(value)

    def get_flag(self, name):
        return self._flags[name]

    def unset_flag(self, name):
        del self._flags[name]

    def has_flag(self, name):
        return name in self._flags.keys()

    def search_for_command(self, cmd_class, start_range = None, end_range = None):
        if end_range is None:
            cmd_slice = self._commands[start_range:]
        elif start_range is None:
            cmd_slice = self._commands
        else:
            cmd_slice = self._commands[start_range:-end_range]
        results = []
        for command in cmd_slice:
            if type(command) == cmd_class:
                results.append(command)
        return results

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
            self._add_command(DialogueCommand(dialogue, self, self._view, self._line_num, self._next_cmd_index))
        else:
            self._add_command(DialogueCommand(line, self, self._view, self._line_num, self._next_cmd_index))

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
        'endtree' : self._construct_endtree}
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
        command = ActiveSpeakerCommand(name, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_alias(self, args):
        if len(args) != 2:
            raise ParseException("Wrong number of arguments encountered on line %d" % self._line_num)
        alias, real_name = args[0], args[1]
        command = AddAliasCommand(alias, real_name, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_set(self, args):
        self._check_arg_size(args, 1, 2)
        name = args[0]
        flag_val = None
        if len(args) > 1:
            flag_val = args[1]
            flag_val = self._autoconvert_flag_value(flag_val)
        command = SetFlagCommand(name, flag_val, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_unset(self, args):
        self._check_arg_size(args, 1, 1)
        name = args[0]
        command = UnsetFlagCommand(name, self, self._view, self._line_num, self._next_cmd_index)
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
            value = self._autoconvert_flag_value(value)
        command = IfCommand(self._next_cmp_id, flag, value, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_elseif(self, args):
        self._check_arg_size(args, 1, 2)
        if self._expecting_endif is False:
            raise ParseException('"elseif" statement found without matching "if" statement on line %d' % self._line_num)
        flag = args[0]
        value = None
        if len(args) > 1:
            value = args[1]
            value = self._autoconvert_flag_value(value)
        command = ElseifCommand(self._next_cmp_id, flag, value, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_else(self, args):
        self._check_arg_size(args, 0, 0)
        if self._expecting_endif is False:
            raise ParseException('"else" statement found without matching "if" statement on line %d' % self._line_num)
        command = ElseCommand(self._next_cmp_id, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_endif(self, args):
        self._check_arg_size(args, 0, 0)
        if self._expecting_endif is False:
            raise ParseException('"endif" statement found without matching "if" statement on line %d' % self._line_num)
        self._expecting_endif = False
        command = EndifCommand(self._next_cmp_id, self, self._view, self._line_num, self._next_cmd_index)
        self._next_cmp_id += 1
        return command

    def _construct_tree(self, args):
        self._check_arg_size(args, 1, 1)
        if self._inside_tree is True:
            raise ParseException('Attempt to nest "tree" statements made on line %d' % self._line_num)
        self._inside_tree = True
        flag_name = args[0]
        command = TreeCommand(self._next_tree_id, flag_name, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_leaf(self, args):
        if len(args) == 0:
            raise ParseException('Attempt to use "leaf" statement without any text made on line %d' % self._line_num)
        if self._inside_tree is False:
            raise ParseException('Attempt to use "leaf" statement outside tree made on line %d' % self._line_num)
        text = " ".join(args)
        command = LeafCommand(self._next_tree_id, text, self, self._view, self._line_num, self._next_cmd_index)
        return command

    def _construct_endtree(self, args):
        self._check_arg_size(args, 0, 0)
        if self._inside_tree is False:
            raise ParseException('Attempt to use "endtree" statement outside of tree made on line %d' % self._line_num)
        self._inside_tree = False
        display_command = DisplayTreeCommand(self._next_tree_id, self, self._view, self._line_num, self._next_cmd_index)
        input_command = GetTreeInputCommand(self._next_tree_id, self, self._view, self._line_num, self._next_cmd_index)
        self._next_tree_id += 1
        # hacky fix to get around building two commands but having to return one
        self._add_command(display_command)
        return input_command

    def _check_arg_size(self, args, low_end, high_end):
        if len(args) > high_end:
            raise ParseException("Too many arguments encountered on line %d" % self._line_num)
        elif len(args) < low_end:
            raise ParseException("Too few arguments encountered on line %d" % self._line_num)

    def _autoconvert_flag_value(self, value):
        if value == None:
            return value
        elif type(value) == int:
            return value
        elif value.isdigit():
            value = int(value)
        return value

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

    def _get_context(self, index):
        return self._contexts[index]

    def _partial_restore_context(self, index):
        context = self._contexts[index]
        new_aliases = context["aliases"]
        new_flags = context["flags"]
        self._aliases = new_aliases
        self._flags = new_flags


class ParseException(Exception):
    pass


class RuntimeCommand(object):

    can_stop_at = False
    save_with_context = False

    def __init__(self, runtime, view, line_num, index):
        self.runtime = runtime
        self.view = view
        self.line_num = line_num
        self.index = index

    def execute(self):
        pass

    def verify(self):
        return True


class DialogueCommand(RuntimeCommand):

    can_stop_at = True

    def __init__(self, dialogue, runtime, view, line_num, index):
        super(DialogueCommand, self).__init__(runtime, view, line_num, index)
        self._dialogue = dialogue

    def execute(self):
        self.view.display_dialogue(self._dialogue)


class ActiveSpeakerCommand(RuntimeCommand):

    save_with_context = True

    def __init__(self, name, runtime, view, line_num, index):
        super(ActiveSpeakerCommand, self).__init__(runtime, view, line_num, index)
        self._name = name

    def execute(self):
        name = self._name
        if self.runtime.has_alias_for(name):
            name = self.runtime.get_alias_for(name)
        self.view.set_speaker(name)


class AddAliasCommand(RuntimeCommand):

    def __init__(self, alias, real_name, runtime, view, line_num, index):
        super(AddAliasCommand, self).__init__(runtime, view, line_num, index)
        self._alias = alias
        self._real_name = real_name

    def execute(self):
        self.runtime.add_alias(self._alias, self._real_name)


class SetFlagCommand(RuntimeCommand):

    def __init__(self, name, value, runtime, view, line_num, index):
        super(SetFlagCommand, self).__init__(runtime, view, line_num, index)
        self._name = name
        self._value = value

    def execute(self):
        self.runtime.set_flag(self._name, self._value)


class UnsetFlagCommand(RuntimeCommand):

    def __init__(self, name, runtime, view, line_num, index):
        super(UnsetFlagCommand, self).__init__(runtime, view, line_num, index)
        self._name = name

    def execute(self):
        self.runtime.unset_flag(self._name)


class IfCommand(RuntimeCommand):

    def __init__(self, cmp_id, flag, cmp_val, runtime, view, line_num, index):
        super(IfCommand, self).__init__(runtime, view, line_num, index)
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

    def __init__(self, cmp_id, runtime, view, line_num, index):
        super(ElseCommand, self).__init__(runtime, view, line_num, index)
        self.cmp_id = cmp_id


class EndifCommand(RuntimeCommand):

    def __init__(self, cmp_id, runtime, view, line_num, index):
        super(EndifCommand, self).__init__(runtime, view, line_num, index)
        self.cmp_id = cmp_id


class TreeCommand(RuntimeCommand):

    can_stop_at = True

    def __init__(self, tree_id, flag_name, runtime, view, line_num, index):
        super(TreeCommand, self).__init__(runtime, view, line_num, index)
        self.tree_id = tree_id
        self.flag_name = flag_name


class LeafCommand(RuntimeCommand):

    def __init__(self, tree_id, choice_text, runtime, view, line_num, index):
        super(LeafCommand, self).__init__(runtime, view, line_num, index)
        self.tree_id = tree_id
        self.choice_text = choice_text


class DisplayTreeCommand(RuntimeCommand):

    def __init__(self, tree_id, runtime, view, line_num, index):
        super(DisplayTreeCommand, self).__init__(runtime, view, line_num, index)
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

    def __init__(self, tree_id, runtime, view, line_num, index):
        super(GetTreeInputCommand, self).__init__(runtime, view, line_num, index)
        self.tree_id = tree_id

    def execute(self):
        flag_name = self._get_flag_name()
        choice = self.view.get_selected_choice()
        self.runtime.set_flag(flag_name, choice)

    def _get_flag_name(self):
        tree = self.runtime.search_for_command(TreeCommand, end_range=self.index)[0]
        return tree.flag_name
