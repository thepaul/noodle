# numbers

(assert (== .23e4 2300.0))
(assert (== 4.23e4 42300.0))
(assert (== 4.e-3 0.004))
(assert (== 0x43 0x043 67))
(assert (== 0123 00123 83))
(assert (== -0.e-3 -.0e-3 -0.0 0))
(assert (== 111 (+ 1 110)))
(assert (== .002e+3 2.0))
(assert (== 4.32e1 4.32e+1 43.2 432e-1 .432e+2 432.e-1 432.0e-1 0.432e+2))
(assert (== 2L 2))
(assert (isinstance 1234L long))
