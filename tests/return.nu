# mid-function return

(define (test-return foo)
  (cond (foo (return foo)) (else 0))
  False)
(assert (== (test-return 12) 12))
(assert (is (test-return []) False))
