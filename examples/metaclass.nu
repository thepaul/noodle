# Using a metaclass to catch any exceptions that occur in all methods of a
# class. Probably a very silly thing to do.

(define (catch-exceptions-in-class exc-to-catch callback)
    (define (make-the-class name bases namespace)
        (type name bases
              (dict (for-list (name v) in (.namespace.items)
                         \(name (if (and (not (.name.startswith '_'))
                                         (callable v))
                                    ((lambda (v) (lambda (@a @@k)
                                        (try (return (v @a @@k))
                                          (except (exc-to-catch)
                                            (return (callback)))))) v)
                                    v)))))))

(import traceback)

# exceptions in methods of A cause a formatted traceback to be returned as
# a string, instead of the normal return value.
(class (A (object))
  (= __metaclass__ (catch-exceptions-in-class Exception .traceback.format_exc))
  (define (get-an-attr self attrname)
      (getattr self attrname)))

(= a (A))
(= .a.an-attr 23)

(print (% "result of (.a.get-an-attr 'an-attr'): %s"
          (repr (.a.get-an-attr 'an-attr'))))
(print (% "result of (.a.get-an-attr 'bad-attr'): %s"
          (repr (.a.get-an-attr 'bad-attr'))))
