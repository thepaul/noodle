# list creation

(= my-list \[0 1 2 3])

(assert (== [my-list 2] 2))
(assert (== [my-list 1:3] \[1 2]))
