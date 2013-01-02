# deletion of subscripts and slices

(define long-list \[0 1 2 3 4 3 2 1 0])
(del [long-list 3])
(assert (== long-list \[0 1 2 4 3 2 1 0]))
(del [long-list 3:-1])
(assert (== long-list \[0 1 2 0]))
