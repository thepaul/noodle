# defmacro

(defmacro (next-5 startnum) `(range ,startnum ,(+ 5 startnum)))
(assert (== (next-5 17) \[17 18 19 20 21]))

# (make sure macros aren't like normal functions; check for any code objects
# among the constants of the code block)
(= macro-using-code (nu-compile `(
    (defmacro (foo bar) 'replacement code')
    (assert (== (foo (w00t w00t)) 'replacement code'))
)))

(for const in .macro-using-code.co_consts
     (assert (not (isinstance const (type macro-using-code)))))
