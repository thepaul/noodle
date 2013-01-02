# tail-call optimization

(define (factorial n)
  (define (iterate n acc)
    (if (<= n 1)
        acc
        (iterate (- n 1) (* acc n))))
  (iterate n 1))
(assert (== (factorial 4) 24))

(define (test-tail-call-opt foo:0)
  (if (== foo 0)
      (test-tail-call-opt (define flag 12))
      (assert (try flag (except (UnboundLocalError) False)))))
(assert (== (test-tail-call-opt) 12))
