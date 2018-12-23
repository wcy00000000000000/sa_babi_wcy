# Created by WCY

"""generate.py: generate SA-bAbI code examples"""

import argparse
import hashlib
import os
import random
import string
import sys
import json

import templates_wcy

# TODO: move away from this ugly hack by merging the conda enviroment in pipeline/ into Docker
#sys_path_parent = os.path.abspath('..')
# if sys_path_parent not in sys.path:
#    sys.path.append(sys_path_parent)
#from classes.sa_tag import Tag
from sa_tag_wcy import Tag

# maximum number of variable names
MAX_NUM_VARS = 10
# variable name template
VAR_STR = "entity_%s"
# maximum number of flow-insensitive case additions
MAX_NUM_DUMMIES = 2
# minimum number of flow-insensitive case additions, in the
# flow-insensitive-only case
MIN_NUM_DUMMIES_TAUTONLY = 1
# maximum length of arrays and index to try accessing
MAX_IDX = 100
# set of available characters to write to buffer
CHARSET = string.digits + string.ascii_letters

# the number of bytes in each hash filename
FNAME_HASHLEN = 5

# command-line argument default values
# number of instances to generate
DEFAULT_NUM_INSTANCES = 12000
# random seed
DEFAULT_SEED = 0


def main(args):
    """With fixed initial seed, generate instances and save as C files

    Args:
        args (argparse.Namespace), with attributes:
            num_instances (int): how many instances to generate
            outdir (str): path to directory to save instances; must exist
            seed (int): seed to use for random.seed(). If -1, then seed by
                default Python seeding

    Returns: 0 if no error
    """
    # check args
    outdir = args.outdir
    seed = int(args.seed)
    num_instances = int(args.num_instances)
    taut_only = args.taut_only
    linear_only = args.linear_only

    # check paths
    outdir = os.path.abspath(os.path.expanduser(outdir))
    if not os.path.isdir(outdir):
        raise OSError("outdir does not exist: '{}'".format(outdir))

    # set seed
    if seed != -1:
        random.seed(seed)

    generators = [gen_cond_example, gen_while_example, gen_for_example]
    if linear_only:
        generators = [gen_tautonly_linear_example]
    num_generators = len(generators)

    # Generate metadata only if the metadata_file argument is present
    generate_metadata = args.metadata_file is not None
    # This dict is used to store instance metadata
    tag_metadata = {}
    inst_num = 0

    while inst_num < num_instances:
        # generate example
        gen = generators[inst_num % num_generators]
        if gen is gen_tautonly_linear_example:
            instance_str, tags = gen()
        else:
            include_cond_ptrfree = not taut_only
            instance_str, tags = gen(
                include_cond_ptrfree=include_cond_ptrfree)

        # generate filename
        byte_obj = bytes(instance_str, 'utf-8')
        fname = hashlib.shake_128(byte_obj).hexdigest(FNAME_HASHLEN)
        fname = "{}.c".format(fname)
        if fname in tag_metadata:
            # Collision, try again
            continue

        # insert record into metadata for this c file
        tag_metadata[fname] = [tag.value for tag in tags]
        inst_num += 1

        # write to file
        path = os.path.join(outdir, fname)
        with open(path, 'w') as f:
            f.write(instance_str)

    if generate_metadata:
        # construct the complete metadata
        metadata = {
            "working_dir": outdir,
            "num_instances": num_instances,
            "tags": tag_metadata
        }
        with open(args.metadata_file, 'w') as f:
            json.dump(metadata, f)

    return 0


def gen_cond_example(include_cond_ptrfree=True):
    """Generate conditional example

    Returns:
        instance_str (str): str of code example
        tags (list of Tag): tag for each line representing buffer safety
    """
    anon_vars = _get_anon_vars()
    ptr, idx_var, thresh_var = anon_vars[:3]
    dummy_vars = anon_vars[3:]
    thresh = random.randrange(MAX_IDX)
    idx_init = random.randrange(MAX_IDX)
    size = random.randrange(MAX_IDX)
    char = _get_char()
    substitutions = {
        'ptr': ptr,
        'idx_var': idx_var,
        'size': size,
        'thresh': thresh,
        'thresh_var': thresh_var,
        'idx_init': idx_init,
        'char': char
    }
    main_lines = templates_wcy.COND_MAIN_LINES
    cond = idx_init < thresh
    safe = (not cond)
    dec_init_pairs = templates_wcy.COND_DEC_INIT_PAIRS

    return _assemble_general_example(dec_init_pairs, main_lines, dummy_vars,
                                     safe, substitutions,
                                     include_cond_ptrfree)


def gen_while_example(include_cond_ptrfree=True):
    """Generate while-loop example

    Returns:
        instance_str (str): str of code example
        tags (list of Tag): tag for each line representing buffer safety
    """
    anon_vars = _get_anon_vars()
    ptr, idx_var, max_var = anon_vars[:3]
    dummy_vars = anon_vars[3:]
    size = random.randrange(MAX_IDX)
    idx_init = random.randrange(MAX_IDX)
    max_idx = random.randrange(MAX_IDX)
    char = _get_char()
    substitutions = {
        'ptr': ptr,
        'idx_var': idx_var,
        'max_var': max_var,
        'size': size,
        'idx_init': idx_init,
        'max_idx': max_idx,
        'char': char
    }
    main_lines = templates_wcy.WHILE_MAIN_LINES
    safe = (idx_init >= max_idx)
    dec_init_pairs = templates_wcy.WHILE_DEC_INIT_PAIRS

    return _assemble_general_example(dec_init_pairs, main_lines, dummy_vars,
                                     safe, substitutions,
                                     include_cond_ptrfree)


def gen_for_example(include_cond_ptrfree=True):
    """Generate for-loop example

    Returns:
        instance_str (str): str of code example
        tags (list of Tag): tag for each line representing buffer safety
    """
    anon_vars = _get_anon_vars()
    ptr, idx_var, max_var = anon_vars[:3]
    dummy_vars = anon_vars[3:]
    size = random.randrange(MAX_IDX)
    idx_init = random.randrange(MAX_IDX)
    max_idx = random.randrange(MAX_IDX)
    char = _get_char()
    substitutions = {
        'ptr': ptr,
        'idx_var': idx_var,
        'max_var': max_var,
        'size': size,
        'idx_init': idx_init,
        'max_idx': max_idx,
        'char': char
    }
    main_lines = templates_wcy.FOR_MAIN_LINES
    safe = (idx_init >= max_idx)
    dec_init_pairs = templates_wcy.FOR_DEC_INIT_PAIRS

    return _assemble_general_example(dec_init_pairs, main_lines, dummy_vars,
                                     safe, substitutions,
                                     include_cond_ptrfree)


def gen_tautonly_linear_example():
    """Generate example with no control flow, only flow-insensitive writes

    Returns:
        instance_str (str): str of code example
        tags (list of Tag): tag for each line representing buffer safety
    """
    # this intentionally has only flow-insensitive buffer writes
    include_cond_ptrfree = False
    dummy_vars = _get_anon_vars()
    substitutions = dict()
    main_lines = []
    safe = None
    dec_init_pairs = []

    return _assemble_general_example(dec_init_pairs, main_lines, dummy_vars,
                                     safe, substitutions,
                                     include_cond_ptrfree)


def _assemble_general_example(dec_init_pairs, main_lines, dummy_vars,
                              safe, substitutions, include_cond_ptrfree):
    """Get instance lines, convert to string, generate tags

    Args:
        dec_init_pairs (list of tuple): declaration/initialization statements,
            e.g. those in templates_wcy.py
        main_lines (list of str): lines with the conditional or loop,
            e.g. those in templates_wcy.py
        dummy_vars (list of str): variable names available for use
        safe (bool): whether the conditional buffer write is safe
        substitutions (dict): names to substitute into templates_wcy
        include_cond_ptrfree (bool): whether to include the
            control flow-sensitive buffer write

    Returns:
        instance_str (str): str of code example
        tags (list of Tag): tag for each line representing buffer safety

    Ensures:
        len(instance_str.split("\n")) == len(tags)
    """
    if include_cond_ptrfree:
        # copy to avoid changing the template list due to aliasing
        main_lines = main_lines[:]
        main_lines += templates_wcy.FREE_LINES
    else:
        safe = None

    lines, body_tags = _get_lines(dec_init_pairs, main_lines,
                                  dummy_vars, safe, include_cond_ptrfree)
    tags = _get_tags(body_tags)
    instance_str = _get_instance_str(lines, substitutions,
                                     templates_wcy.FUNC_TMPL_STR, tags)
    return instance_str, tags


def _get_anon_vars():
    """Get list of unique, anonymized variable names in random order

    Returns:
        anon_vars (list of str)
    """
    anon_vars = [VAR_STR % itm for itm in range(MAX_NUM_VARS)]
    random.shuffle(anon_vars)
    return anon_vars


def _get_full_template(setup_lines, partial_template):
    """Shuffle the setup lines and merge them into partial template

    Args:
        setup_lines (list of str): list of lines of setup code (declarations)
        partial_template (str): code template that needs setup

    Returns:
        full_template (string.Template instance): with setup subbed in
    """
    random.shuffle(setup_lines)
    setup_str = '\n'.join("    " + itm for itm in setup_lines)
    mapping = {'setup': setup_str}
    full_template = string.Template(partial_template)
    full_template_str = full_template.safe_substitute(mapping)
    full_template = string.Template(full_template_str)
    return full_template


def _get_char():
    """Get a random single character

    Returns:
        char (str): random single character from charset
    """
    char = random.choice(CHARSET)
    return char


def _get_lines(dec_init_pairs, main_lines, dummy_vars, safe,
               include_cond_ptrfree):
    """Create full body lines with setup, main content, and dummy interaction

    Args:
        dec_init_pairs (list of tuple)
        main_lines (list of str): lines that use the declared vars
        dummy_vars (list of str): variable names available for dummy use
        safe (bool): whether the query line access is safe (for tags)
            or None, if no conditional query line should be added
        include_cond_ptrfree (bool): whether to include the
            control flow-sensitive buffer write

    Returns:
        lines (list of str)
        body_tags (list of Tag instances): tags for each body line
    """
    setup_lines = _get_setup_lines(dec_init_pairs)
    lines = setup_lines + main_lines

    # construct body tags before adding dummies
    body_tags = [Tag.BODY for _ in lines]
    if include_cond_ptrfree:
        query_tag = Tag.POINTER_FREE_COND_SAFE if safe else Tag.POINTER_FREE_COND_UNSAFE
        body_tags[-1] = query_tag

    min_num_dummies = 0 if include_cond_ptrfree else MIN_NUM_DUMMIES_TAUTONLY
    num_dummies = random.randrange(min_num_dummies, MAX_NUM_DUMMIES + 1)
    lines, body_tags = _insert_dummies(
        setup_lines, main_lines, dummy_vars, num_dummies, body_tags,
        include_cond_ptrfree)

    return lines, body_tags


def _get_setup_lines(dec_init_pairs):
    """Get setup lines (declaring and initializing variables) in random order
    so that variables are declared before initialized. If the second entry of
    the tuple is None, this line only needs to be declared, not initialized,
    e.g. for char arrays.

    The point of this is that the variables collectively can be declared
    and initialized in any order, as long as each variable is declared
    before it is initialized.

    E.g. dec_init_pairs = [("int $idx_var;", "$idx_var = $idx_init;"),
                           ("char $buf_var[$buf_len];", None)]
         _get_setup_lines(dec_init_pairs) could be any of
         ["int $idx_var;", "$idx_var = $idx_init;", "char $buf_var[$buf_len];"]
         ["int $idx_var;", "char $buf_var[$buf_len];", "$idx_var = $idx_init;"]
         ["char $buf_var[$buf_len];", "int $idx_var;", "$idx_var = $idx_init;"]

    Args:
        dec_init_pairs (list of tuple)

    Returns:
        setup_lines (list of str)
    """
    setup_lines = []
    for (dec_str, init_str) in dec_init_pairs:
        if init_str is None:
            idx = random.randrange(len(setup_lines) + 1)
            setup_lines = setup_lines[:idx] + [dec_str] + setup_lines[idx:]
        else:
            idxes = sorted(
                [random.randrange(len(setup_lines) + 1) for _ in range(2)])
            setup_lines = (setup_lines[:idxes[0]] + [dec_str] +
                           setup_lines[idxes[0]:idxes[1]] + [init_str] +
                           setup_lines[idxes[1]:])

    return setup_lines


def _insert_dummies(setup_lines, main_lines, dummy_vars, num_dummies,
                    body_tags, include_cond_ptrfree):
    """Insert dummy array declare/set pairs (all safe sets)

    Args:
        setup_lines (list of str): declaration and initialization lines
        main_lines (list of str): control flow lines
        dummy_vars (list of str): variable names available for dummy use
        num_dummies (int): number of dummy vars to insert
        body_tags (list of Tag instances): tags before adding dummies
        include_cond_ptrfree (bool): whether to include the
            control flow-sensitive pointer free

    Returns:
        lines (list of str): with dummy dec/set pairs added
        body_tags (list of Tag instances): with tags added for dummy lines
    """
    lines = setup_lines + main_lines

    # first line of control flow, inclusive
    control_flow_start = len(setup_lines)
    # last line of control flow, exclusive
    control_flow_end = len(setup_lines + main_lines)
    if include_cond_ptrfree:
        control_flow_end -= 1

    for _ in range(num_dummies):
        (lines, dummy_vars, body_tags, control_flow_start, control_flow_end
         ) = _insert_referential_dummy(
            lines, dummy_vars, body_tags, control_flow_start,
            control_flow_end)

    return lines, body_tags


def _insert_referential_dummy(lines, dummy_vars, body_tags,
                              control_flow_start, control_flow_end,
                              require_safe=False):
    """Insert dummy declare/set lines with referential index access
    E.g. char entity_0[10];
         int entity_1;
         entity_1 = 5;
         entity_0[entity_1] = 'a';

    The char and int declarations happen first in a random order, followed by
    the int initialization and the buffer set.

    Args:
        lines (list of str): lines to insert dummy lines around
        dummy_vars (list of str): variable names available for dummy use
        body_tags (list of Tag instance): body tags before adding dummies
        control_flow_start (int): first idx of control flow lines
        control_flow_end (int): last idx of control flow lines
        require_safe (bool): if True, then require that dummy accesses are
            all safe


    Returns:
         lines (list of str): with dummy dec/set pair added
         dummy_vars (list of str): with used dummy varnames removed
         body_tags (list of Tag instance): with dummy tags added
         control_flow_start (int): updated from args
         control_flow_end (int): updated from args
    """
    if len(dummy_vars) < 2:
        raise ValueError("Trying to insert more dummy vars than available")

    if require_safe:
        dum_len = random.randrange(1, MAX_IDX)
        dum_max = random.randrange(MAX_IDX)
        dum_idx = random.randrange(dum_max)
    else:
        dum_len = random.randrange(MAX_IDX)
        dum_idx = random.randrange(MAX_IDX)
        dum_max = random.randrange(MAX_IDX)

    dum_buf_var = dummy_vars.pop()
    dum_int_var = dummy_vars.pop()
    idx_dec_line = "int %s;" % dum_int_var
    idx_init_line = "%s = %s;" % (dum_int_var, dum_idx)
    ptr_init_line = "char * %s = (char*) malloc(%s);" % (dum_buf_var, dum_len)
    ptr_free_line = "free(%s)" % dum_buf_var
    if_cond_line = "if(%s<%s)" % (dum_idx, dum_max)
    malloc_line = "$ptr = (char*) malloc($size);"

    # idx declaration must go before idx initialization
    setup_lines = [idx_dec_line, idx_init_line]
    # buffer declaration can go anywhere between them
    buf_dec_idx = random.randrange(3)
    setup_lines = (setup_lines[:buf_dec_idx] + [ptr_init_line] +
                   setup_lines[buf_dec_idx:])
    # conditional malloc lines
    malloc_cond_lines = [if_cond_line, malloc_line]
    # whether these setup lines go before the control flow lines
    before_control_flow = random.choice([True, False])
    if before_control_flow:
        range_start = 0
        range_end = control_flow_start + 1
    else:
        range_start = control_flow_end
        range_end = len(lines) + 1

    # lines where buffer and index are declared; index is initialized
    setup_idxes = sorted([random.randrange(range_start, range_end)
                          for _ in range(3)])
    # line where buffer is set
    buf_set_idx = random.randrange(max(setup_idxes), len(lines) + 1)

    # the amounts by which control_flow_{start, end} increase
    # after inserting these lines
    d_start = 0
    d_end = 0
    for idx in setup_idxes + [buf_set_idx]:
        if idx <= control_flow_start:
            d_start += 1
        if idx < control_flow_end:
            d_end += 1
    control_flow_start += d_start
    control_flow_end += d_end

    lines = (lines[:setup_idxes[0]] + [setup_lines[0]] +
             lines[setup_idxes[0]:setup_idxes[1]] + [setup_lines[1]] +
             lines[setup_idxes[1]:setup_idxes[2]] + [setup_lines[2]]+[ptr_free_line] +
             [malloc_cond_lines[0]]+[malloc_cond_lines[1]] +
             lines[setup_idxes[2]:buf_set_idx] + [ptr_free_line] +
             lines[buf_set_idx:])

    safe = dum_idx < dum_max
    ptrfree_tag = Tag.POINTER_FREE_TAUT_SAFE if safe else Tag.POINTER_FREE_TAUT_UNSAFE

    body_tags = (body_tags[:setup_idxes[0]] + [Tag.BODY] +
                 body_tags[setup_idxes[0]:setup_idxes[1]] + [Tag.BODY] +
                 body_tags[setup_idxes[1]:setup_idxes[2]] + [Tag.BODY] + Tag.POINTER_FREE_TAUT_SAFE +
                 [Tag.BODY] + [Tag.BODY] +
                 body_tags[setup_idxes[2]:buf_set_idx] + [ptrfree_tag] +
                 body_tags[buf_set_idx:])

    return lines, dummy_vars, body_tags, control_flow_start, control_flow_end


def _get_instance_str(lines, substitutions, func_tmpl_str, tags,
                      tags_as_comments=True):
    """Make substitutions and construct function instance string

    Args:
        lines (list of str): lines in body, to be substituted
        substitutions (dict)
        func_tmpl_str (str): string for function template to substitute
        tags (list of Tag)
        tags_as_comments (bool): if True, then add the tag as a comment at the
            end of each line

    Returns:
        instance_str (str): complete function as string
    """
    lines = [string.Template(itm).substitute(substitutions) for itm in lines]
    body = "\n".join("    " + line for line in lines)
    substitutions['body'] = body
    instance_str = string.Template(func_tmpl_str).substitute(substitutions)

    if tags_as_comments:
        lines = instance_str.split("\n")
        max_linelen = max(len(line) for line in lines)
        fmt_str = "{:<{width}} // {}"
        lines = [fmt_str.format(line, tag, width=max_linelen)
                 for (line, tag) in zip(lines, tags)]
        instance_str = "\n".join(lines)

    return instance_str


def _get_tags(body_tags):
    """Get full list of tags by adding wrappers

    Args:
        body_tags (list of Tag instances): for body lines only

    Returns:
        tags (list of Tag instances): for full function
    """
    #        #include... int main()    {
    tags = ([Tag.OTHER, Tag.OTHER, Tag.OTHER] +
            body_tags +
            # return 0;     }
            [Tag.BODY, Tag.OTHER])
    return tags


def _test(verbose=False):
    """Test minimally that each generator creates code

    Args:
        verbose (bool): if True, print generated code example
    """
    num_tests_each = 10

    def run_tests(gen, kwargs=None):
        for test_num in range(num_tests_each):
            if kwargs is None:
                instance_str, tags = gen()
            else:
                instance_str, tags = gen(**kwargs)

            if verbose and test_num == 0:
                if kwargs is not None:
                    print("{} {}".format(gen.__name__, kwargs))
                else:
                    print(gen.__name__)
                print(instance_str + "\n")

            assert(isinstance(instance_str, str))
            assert(isinstance(tags, list))
            for itm in tags:
                assert(isinstance(itm, Tag))

            cond_in_tags = (Tag.POINTER_FREE_COND_UNSAFE in tags or
                            Tag.POINTER_FREE_COND_SAFE in tags)
            taut_in_tags = (Tag.POINTER_FREE_TAUT_UNSAFE in tags or
                            Tag.POINTER_FREE_TAUT_SAFE in tags)

            if kwargs is not None:
                if kwargs['include_cond_ptrfree']:
                    assert cond_in_tags
                else:
                    assert(not cond_in_tags)
                    assert taut_in_tags
            else:
                assert taut_in_tags

    for gen in [gen_cond_example, gen_while_example, gen_for_example]:

        kwargs = {"include_cond_ptrfree": True}
        run_tests(gen, kwargs=kwargs)

        kwargs = {"include_cond_ptrfree": False}
        run_tests(gen, kwargs=kwargs)

    run_tests(gen_tautonly_linear_example)


def _get_args():
    """Get command-line arguments"""
    separator = '\n' + "#" * 79 + '\n'
    parser = argparse.ArgumentParser(
        description=__doc__ + separator,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('outdir',
                        help=("(str) Path to directory to write instance.c files to. Must "
                              "exist before running"),
                        metavar="<path>")

    parser.add_argument('-num_instances',
                        help=("(int) Number of instance.c files to create; default "
                              "{}".format(DEFAULT_NUM_INSTANCES)),
                        default=DEFAULT_NUM_INSTANCES,
                        metavar="<int>")

    parser.add_argument('-seed',
                        help=("(int) Seed for random number generator, to reproduce results; "
                              "default {}. If -1 is passed, then use default Python "
                              "seed".format(DEFAULT_SEED)),
                        default=DEFAULT_SEED,
                        metavar="<int>")

    parser.add_argument('-metadata_file',
                        help=("(str) Path to a file which shall be used to store simple "
                              "json metadata about the generated instances"),
                        metavar="<path>")

    parser.add_argument('--taut_only',
                        action='store_true',
                        help=("If passed, then generate examples with only flow-insensitive "
                              "buffer writes"))

    parser.add_argument('--linear_only',
                        action='store_true',
                        help="If passed, then generate only flow-insensitive linear examples")

    args = parser.parse_args()
    return args


_test()

if __name__ == '__main__':
    RET = main(_get_args())
    sys.exit(RET)
