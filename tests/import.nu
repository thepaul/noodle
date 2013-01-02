# import

(assert (is-not (import-from types ModuleType) None))
(assert (isinstance (import re) ModuleType))

# imported names properly becoming global
(assert ((lambda () (.re.compile r'^abc*$'))))

(define regex (.re.compile r'^a*b?c*$' .re.I))
(assert (.regex.search 'aaaaac'))
(assert (.regex.search 'b'))
(assert (is None (.regex.search 'abbc')))

(for a_module in (import sys time struct)
    (assert (isinstance a_module ModuleType)))

(define (all-equal @args)
    (for a in [args 1:] (if (!= a [args 0]) (return False)))
    True)

(assert (all-equal @(for-list var in (import-from re I L M S U X)
                              (type var))))

(import .os.path)
(assert os)
(assert (isinstance .os.path ModuleType))

(assert (== (import-from .os.path basename split)
            \(basename split)))

(import-all-from new cmd)
(assert function) # from new
(assert Cmd) # from cmd
