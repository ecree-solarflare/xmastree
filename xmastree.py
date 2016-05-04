#!/usr/bin/python
# Audit kernel patches or code for "Reverse Christmas Tree" compliance

import sys

# 'bool' is not really primitive, but it's an omnipresent typedef
# 'float' and 'double' are C primitive types, but should not be used in
# kernel code.
# While 'void' is a type, C does not permit declaring a variable of type
# void.  The Standard does not give a rationale for this.
primitive_types = ['signed', 'unsigned', 'char', 'short', 'int', 'long',
                   'bool', 'float', 'double', 'struct', 'union', 'enum']
# Of course this list is non-exhaustive.  Fortunately the vast majority
# of kernel types are bare structs rather than typedefs.
kernel_typedefs = ['u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64',
                   'cpumask_var_t']
# I don't think declaring an extern variable inside a function is legal,
# but let's count it as a declaration nonetheless.
storage_classes = ['auto', 'static', 'register', 'extern']
# Similarly, I'm not sure you can declare restricted variables outside of
# a function parameter list, but language lawyering is not this script's
# job, so let's just handle it anyway.
type_qualifiers = ['const', 'volatile', 'restrict']

def is_decl(line):
    """Determine whether a line looks like it's declaring a variable.
    
    A declaration begins with a type name, a storage-class, or a type
    qualifier.  No sanely-formatted non-declaration should ever do so.
    """
    decl_openers = (primitive_types + kernel_typedefs + storage_classes +
                    type_qualifiers)
    # Get first word in line
    word, _, _ = line.partition(' ')
    return word in decl_openers

last_decl = None
in_comment = False

for line in sys.stdin.readlines():
    # If it's a diff, we want lines starting with + or space, but not -,
    # and we want to strip the leading + before parsing further.
    # If it's not a diff, we want all lines, but no line should ever
    # start with -, nor be indented by a single space.
    if line.startswith('-'):
        continue
    plus = False
    if line.startswith('+') or line.startswith(' '):
        plus = line[0] == '+'
        line = line[1:]
    # If we're not at least a single tab indented, we can't be inside a
    # function, so ignore (and clear state)
    if not line.startswith('\t'):
        last_decl = None
        continue
    co = line.count('/*')
    cc = line.count('*/')
    if co > cc: in_comment = True
    if cc > co: in_comment = False
    if in_comment:
        continue
    # Remove whitespace, now we're done looking at indentation
    line = line.strip()
    if is_decl(line):
        if last_decl is not None and (plus or last_decl[1]):
            if len(line) > len(last_decl[0]):
                print "WARNING: Reverse Christmas Tree Violation"
                print '\t'+last_decl[0]
                print '\t'+line
        last_decl = (line, plus)
    elif line.startswith('/*'):
        # Assume the whole line is a comment
        pass
    elif line:
        last_decl = None
