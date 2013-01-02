# try

# exception catching
(= exception-passed False)
(try (import mongtong)
  (except (ImportError)
    (= exception-passed True)))
(assert exception-passed)

# exception from a few levels down:
(assert
  (==
    (try (begin
           (define (raise-function) (raise (ValueError "moo")))
           (raise-function))
      (except (NameError e)
        "This shouldn't have happened.")
      (except (ValueError e)
        (+ (str e) "foo"))
      (else
        "This shouldn't have happened."))
    "moofoo"))

# no exception raised:
(try 1 (except () (assert False "What's going on?")))

# situation that caused some stacklevel issues before
(assert
  (is None
      (try blah
        (except (AttributeError) 'yes')
        (except (None) (raise))
        (except ()))))
