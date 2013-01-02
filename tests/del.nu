# deletion

(= delete-me 49)
(try (begin
       (del delete-me)
       delete-me)
     (except (NameError) (comment do nothing))
     (else (assert False)))

(try
  (let ((one 1))
    (del one)
    one)
  (except (NameError) (comment do nothing))
  (else (assert False)))
