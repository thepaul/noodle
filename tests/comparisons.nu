# comparisons

(assert (> 9 8 3 2 1))
(assert (not (> 9 8 3 2 3)))
(assert (> 9 8))
(assert (in 5 \(1 6 2 3 5 2 'nine')))
(assert (not-in 5 \[3 2 1 6 4 2 7]))
(assert (!= 1 2 3 4 3 2 1))
(assert (< (- 4) -3 -2 0 19))
(assert (<= (- 4) -4))
(assert (>= 3 2 -100e4))
(assert (not (>= 2 3 2)))
