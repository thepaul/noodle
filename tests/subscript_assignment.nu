# assigning to subscripts

(= numberlist \[0 1 2 3 4])
(= [numberlist 2] 6)
(assert (== [numberlist 2] 6))
(assert (== numberlist \[0 1 6 3 4]))
