# function varargs accepting

(define (sum-numbers @nums) (sum nums))
(define num-list \[10 29 100 .24 -1e3])
# function varargs calling
(assert (== (sum-numbers @num-list) (+ 10 29 100 .24 -1e3)))
