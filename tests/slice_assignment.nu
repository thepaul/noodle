# assigning to slices

(define numberlist \[0 1 2])

(assert (== (= [numberlist 2:] \[10 11 12 13]) \[10 11 12 13]))
(assert (== [numberlist 2:] \[10 11 12 13]))
(assert (== numberlist \[0 1 10 11 12 13]))
