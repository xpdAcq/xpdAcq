
import sys

def _graceful_exit(error_message):
    try:
        raise RuntimeError(error_message)
        return 0
    except Exception as err:
        sys.stderr.write('WHOOPS: {}'.format(str(err)))
        return 1

def composition_analysis(compstring):
    """Pulls out elements and their ratios from the config file.

    compstring   -- chemical composition of the sample, e.g.,
                    "NaCl", "H2SO4", "La0.5 Ca0.5 Mn O3".  Blank
                    characters are ignored, unit counts can be omitted.
                    It is critical to use proper upper-lower case for atom
                    symbols as this is used to delimit them in the formula.

    Returns a list of atom symbols and a corresponding list of their counts.
    """
    import re
    # remove all blanks
    compbare = re.sub('\s', '', compstring)
    # reusable error message
    # make sure there is at least one uppercase character in the compstring
    upcasechars = any(str.isupper(c) for c in compbare)
    if not upcasechars and compbare:
        emsg = 'invalid chemical composition "%s"' % compstring
        raise ValueError(emsg)
    # split at every upper-case letter, possibly followed by a lower case
    # one and charge specification
    namefracs = re.split('([A-Z][a-z]?(?:[1-8]?[+-])?)', compbare)[1:]
    names = namefracs[0::2]
    # use unit count when empty, convert to float otherwise
    getfraction = lambda s: (s == '' and 1.0 or float(s))
    fractions = [getfraction(w) for w in namefracs[1::2]]
    return names, fractions

def _RE_state_wrapper(RE_obj):
    ''' a wrapper to check state of bluesky runengine object after pausing

        it provides control to stop/abort/resume runengine under current package structure
    '''
    usr_input = input('')
    # while loop gives chance to iteratively confirm user's input
    while RE_obj.state == 'paused':
        if usr_input in ('resume()'):
            RE_obj.resume()
        elif usr_input in ('abort()'):
            abort_all = input('''current scan will be aborted. Do you want to abort all successive scans (if you are running a script)? y/[n]  ''')
            while True:
                if abort_all in ('y', 'yes'):
                    sys.exit(_graceful_exit('''INFO: All successive scans are aborted'''))
                elif abort_all in ('n', 'no'):
                    print('''INFO: Current scan is aborted and successive ones are kept''')
                    RE_obj.abort()
                else:
                    print('please reenter your input')
        elif usr_input in ('stop()'):
            RE_obj.stop()
        else:
            print('please renter your input')
