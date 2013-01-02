# try-else:
(assert (== (try 1 (except () (assert False)) (else 27)) 27))

# catch-all exception:
(assert (== (try (raise TypeError) (except () 23) (else 4)) 23))
