# quasiquote/unquote

(= deref-me '42')
(= mytuples `(mktuple {} (int ,deref-me)))
(assert (== (len mytuples) 3))
(assert (== (len [mytuples 1]) 1))
(assert (== (len [mytuples 2]) 2))
(assert (== [mytuples 1] \((mksymbol 'mkdict'))))
(assert (== [[mytuples 2] -1] '42'))
