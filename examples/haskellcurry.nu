(define (curry func)
  (= collected_args [])
  (= collected_kwargs {})
  (define (curried @args @@kwargs)
    (if args (.collected_args.extend args))
    (if kwargs (.collected_kwargs.update kwargs))
    (if (or args kwargs)
        curried
        (func @collected_args @@collected_kwargs)))
  (try
      (= .curried.func_name .func.func_name)
    (except (AttributeError)))
  curried)

(= myfunc (curry (lambda (@a) (tuple a))))

(print (((((myfunc 2) 3) 4) 5 6 7)))
