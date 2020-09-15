import dsdobjects.objectio as oio
from dsdobjects.utils import natural_sort

from . import __version__
from .crnutils import genCRN, genCON
from .objects import (NuskellDomain, 
                      NuskellComplex,
                      NuskellMacrostate,
                      NuskellReaction) 

def get_domains(complexes):
    """ Return a set of domains present in the TestTube. """
    domains = set()
    [domains.add(d) for cplx in complexes for d in cplx.domains]
    return list(domains)

def get_strands(complexes):
    """ Return a set of strands present in the TestTube. """
    strands = set()
    [strands.add(tuple(s)) for cplx in complexes.values() for s in cplx.lol_sequence]
    return strands

def load_pil(data, is_file = False):
    """ Parses a string or file written in PIL notation! """
    oio.LogicDomain = NuskellDomain
    oio.Complex = NuskellComplex
    oio.Reaction = NuskellReaction
    oio.Macrostate = NuskellMacrostate

    doms, cplxs, rms, det, con = oio.read_pil(data, is_file)
    return doms, cplxs, rms, det, con 


def write_pil(solution, reactions, fh = None, molarity = 'nM', crn = None, fsc = None, ts = None):
    """ Write the contents of solution into a PIL file (kernel notation).

    Args:
        solution (dict): A dictionary containing all the complexes in solution.
        fh (filehandle): A filehandle that the output is written to or None.
        molarity (str, optional): Specify a molarity of concentrations (M, mM, uM, nM, pM).
        crn (list[list], optional): a nuskell-style CRN expression
        fsc (dict, optional): formal species and their concentrations.
        ts (str, optional): name of the translation scheme

    Example:
        length d1 = 6
        length d2 = 4
        length h3 = 1
        cplx1 = h3 d1( d2( + )) @ initial 10 nM
    """

    out = []
    def output_string(string):
        if fh is None:
            out.append(string)
        else :
            fh.write(string)

    # Write header #
    output_string("# File generated by nuskell-{}\n".format(__version__))
    output_string("#\n")
    if ts:
        output_string("# - Translation Scheme: {}\n".format(ts))
        output_string("#\n")
    if fsc:
        output_string("# - Input concentrations: \n")
        for ico in genCON(fsc):
            output_string('#    {}\n'.format(ico))
        output_string("#\n")
    if crn:
        output_string("# - Input CRN: \n")
        for rxn in genCRN(crn):
            output_string('#    {}\n'.format(rxn))
        output_string("#\n")

    # Print Domains
    output_string("\n# Domain Specifications\n")
    seen = set()
    domains = get_domains(solution.values())
    for d in natural_sort(domains):
        if d.is_complement:
            dom = ~d
        else :
            dom = d
        if dom not in seen:
            output_string("length {:s} = {:d}\n".format(dom.name, dom.length))
            seen.add(dom)

    sc = natural_sort([x for x in solution.values() if x.name[0] not in ('f', 'i', 'w')])
    fc = natural_sort([x for x in solution.values() if x.name[0] == 'f'])
    ic = natural_sort([x for x in solution.values() if x.name[0] == 'i'])
    wc = natural_sort([x for x in solution.values() if x.name[0] == 'w'])

    def print_cplxs(cl):
        for cplx in cl:
            if cplx.concentration:
                output_string("{:s} = {:s} @{} {} {}\n".format(cplx.name, 
                    cplx.kernel_string, *cplx.concentrationformat(molarity)))
            else:
                output_string("{:s} = {:s}\n".format(cplx.name, cplx.kernel_string))
 
    if len(sc):
        output_string("\n# Signal complexes ({})\n".format(len(sc)))
        print_cplxs(sc)

    if len(fc):
        output_string("\n# Fuel complexes ({})\n".format(len(fc)))
        print_cplxs(fc)

    if len(ic + wc):
        output_string("\n# Other complexes ({})\n".format(len(ic + wc)))
        print_cplxs(ic)
        print_cplxs(wc)

    if reactions is not None:
        output_string("\n# Reactions ({})\n".format(len(reactions)))
        for rxn in natural_sort(reactions):
            output_string("reaction {:s}\n".format(rxn.full_string(molarity, 's')))

    return ''.join(out)

def write_vdsd(solution, fh = None, molarity = 'nM', crn = None, fsc = None, ts = None):
    """ Write the contents of solution into VisualDSD \*.dna format.

    Args:
        solution (dict): A dictionary containing all the complexes in solution.
        fh (filehandle): A filehandle that the output is written to or None.
        molarity (str, optional): Specify a molarity of concentrations (M, mM, uM, nM, pM).
        crn (list[list], optional): a nuskell-style CRN expression
        fsc (dict, optional): formal species and their concentrations.
        ts (str, optional): name of the translation scheme

    Note:
        This function assumes that toehold domains are named starting with a 't',
        history domains start with a 'h' and anti-sense domains end with '*'.
    """

    out = []
    def output_string(string):
        if fh is None:
            out.append(string)
        else :
            fh.write(string)

    def pair_table(ss, chars=['.']):
        """ Return a secondary struture in form of pair table:
    
        Args:
          ss (str): secondary structure in dot-bracket format
          chars (list, optional): a list of characters that are ignored. Defaults to
            ['.']
    
        Example:
           ((..)). => [5,4,-1,-1,1,0,-1]
    
        Raises:
           NuskellObjectError: Too many closing brackets in secondary structure.
           NuskellObjectError: Too many opening brackets in secondary structure.
           NuskellObjectError: Unexpected character in sequence: "{}"
    
        Returns:
          [list]: A pair-table
        """
        stack = []
    
        pt = [-1] * len(ss)
    
        for i, char in enumerate(ss):
            if (char == '('):
                stack.append(i)
            elif (char == ')'):
                try:
                    j = stack.pop()
                except IndexError as e:
                    raise NuskellObjectError(
                        "Too many closing brackets in secondary structure")
                pt[i] = j
                pt[j] = i
            elif (char == '+'):
                pt[i] = '+'
            elif (char not in set(chars)):
                raise NuskellObjectError(
                    "Unexpected character in sequence: '" + char + "'")
    
        if stack != []:
            raise NuskellObjectError(
                "Too many opening brackets in secondary structure")
        return pt

    output_string("(* File generated by nuskell-{}\n".format(__version__))

    if ts:
        output_string("\n - Translation Scheme: {}".format(ts))
    if fsc:
        output_string("\n - Input concentrations:")
        for ico in genCON(fsc):
            output_string('\n    {}'.format(ico))
        output_string("\n")
    if crn:
        output_string("\n - Input CRN:")
        for rxn in genCRN(crn):
            output_string('\n    {}'.format(rxn))
        output_string("\n")
    output_string("\n   Please adjust counts/concentrations manually.\n".format(__version__))
    output_string("*)\n\n".format(crn))

    output_string("def Fuel = 20\n")
    output_string("def Signal = 5\n\n")

    sc = natural_sort([x for x in solution.values() if x.name[0] not in ('f', 'i', 'w')])
    fc = natural_sort([x for x in solution.values() if x.name[0] == 'f'])
    ic = natural_sort([x for x in solution.values() if x.name[0] == 'i'])
    wc = natural_sort([x for x in solution.values() if x.name[0] == 'w'])

    for e, cplx in enumerate(sc + fc + ic + wc):
        if e == 0:
            output_string('( ')
        else:
            output_string('| ')

        if cplx in sc: # not the most efficient way ...
            output_string("Signal * ")
        else:
            output_string("constant Fuel * ")

        name = cplx.name
        sequ = cplx.sequence
        stru = cplx.structure

        ptab = pair_table(stru)

        dnaexpr = [[]]
        pos = 0
        for e, d in enumerate(ptab):
            if d == '+':
                flag = 'top' if flag == 'bound' else flag
                expr = 'cut'

            elif d == -1:
                toe = '^' if sequ[e].name[0] == 't' else ''
                if sequ[e].name[-1] == '*':
                    flag = 'bottom'
                    expr = sequ[e].name[:-1] + toe + '*'
                elif sequ[e].name[0] == 'h':
                    flag = 'top'
                    expr = '_'
                else:
                    flag = 'top'
                    expr = sequ[e].name + toe

            elif d > e:  # '('
                flag = 'bound'
                toe = '^' if sequ[e].name[0] == 't' else ''
                if sequ[e].name[-1] == '*':
                    expr = sequ[e].name[:-1] + toe + '*'
                elif sequ[e].name[0] == 'h':
                    raise NuskellObjectError('Unexpected bound history domain.')
                else:
                    expr = sequ[e].name + toe

                dnaexpr.append([])
                pos += 1

            elif d < e:  # ')'
                flag = 'bottom'
                expr = None
                pos -= 1
                if pos < 0:
                    raise NuskellObjectError('too many closing base-pairs')
                continue
            else:
                raise NuskellObjectError(f'strange case: {e}, {d}')

            if dnaexpr[pos] == []:
                dnaexpr[pos] = [[flag, expr]]
            else:
                dnaexpr[pos].append([flag, expr])

        # decode dnaexpr
        dnaflat = []
        for d in dnaexpr:
            for dd in d:
                dnaflat.append(dd)

        # PRINT TO FILE
        close = None
        for e, d in enumerate(dnaflat):
            if d[1] == 'cut':
                output_string(close)
                close = None
                if e == len(dnaflat) - 1:
                    continue
                if d[0] == 'bottom':
                    output_string('::')
                else:
                    output_string(':')
                continue

            if d[0] == 'bottom':
                if close is None:
                    output_string('{')
                    close = '}'
                elif close == ']' or close == '>':
                    output_string('{}{'.format(close))
                    close = '}'

            if d[0] == 'bound':
                if close is None:
                    output_string('[')
                    close = ']'
                elif close == '}' or close == '>':
                    output_string('{}['.format(close))
                    close = ']'

            if d[0] == 'top':
                if close is None:
                    output_string('<')
                    close = '>'
                elif close == '}' or close == ']':
                    output_string('{}<'.format(close))
                    close = '>'
            output_string(" {} ".format(d[1]))
        if close:
            output_string("{} (* {} *)\n".format(close, name))
        else:
            output_string(" (* {} *)\n".format(name))

    output_string(")\n")
    return ''.join(out)
      
