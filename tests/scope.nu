# difference between = and define
(define (make-prop init: None)
  (= var init)
  (define (set-var newval)
    # var is assigned before being accessed--in normal Python, that would
    # make it a local, but in Noodle, it can still be a free variable (and
    # is in this case)
    (= var newval)
    var)
  (define (get-var) var)
  \(set-var get-var))

(= (setter getter) (make-prop))
(assert (== (getter) None))
(setter 12)
(assert (== (getter) 12))

# This is the same function body as above, except with define instead of =.
(define (make-prop-2 init: None)
  (= var init)
  (define (set-var newval)
    # var is here set with the define macro--so while it would be a free
    # variable normally, define forces it to be local, so doing this setting
    # does not change the var in the enclosing scope.
    (define var newval)
    var)
  (define (get-var) var)
  \(set-var get-var))

(= (setter getter) (make-prop-2))
(assert (== (getter) None))
(setter 12)
(assert (== (getter) None))
